import re

import easyocr

reader = None


def get_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(["vi", "en"], gpu=False)
    return reader


def extract_text(image_path: str) -> str:
    """Extract text from receipt image with horizontal line merging.

    Uses EasyOCR bounding boxes to group fragments sharing the same
    horizontal line, producing cleaner line-by-line output.
    """
    r = get_reader()
    results = r.readtext(image_path, detail=1)
    if not results:
        return ""

    fragments = []
    for bbox, text, _conf in results:
        y_center = sum(pt[1] for pt in bbox) / 4
        x_left = min(pt[0] for pt in bbox)
        height = max(pt[1] for pt in bbox) - min(pt[1] for pt in bbox)
        fragments.append({
            "text": text.strip(),
            "y_center": y_center,
            "x_left": x_left,
            "height": max(height, 1),
        })

    fragments.sort(key=lambda f: f["y_center"])

    avg_height = sum(f["height"] for f in fragments) / len(fragments)
    threshold = max(avg_height * 0.5, 10)

    merged_lines: list[str] = []
    current_line = [fragments[0]]

    for frag in fragments[1:]:
        if abs(frag["y_center"] - current_line[0]["y_center"]) <= threshold:
            current_line.append(frag)
        else:
            current_line.sort(key=lambda f: f["x_left"])
            merged_lines.append("  ".join(f["text"] for f in current_line))
            current_line = [frag]

    current_line.sort(key=lambda f: f["x_left"])
    merged_lines.append("  ".join(f["text"] for f in current_line))

    return "\n".join(merged_lines)


def _normalize_ocr_text(raw_text: str) -> str:
    """Clean up common OCR artifacts: spaces inside numbers, stray punctuation."""
    text = raw_text
    # Fix spaces inside numbers like "216 , 000" -> "216,000" or "8 , 760 , 000" -> "8,760,000"
    text = re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", text)
    # Fix spaces inside numbers with dots like "45. 000" -> "45.000"
    text = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", text)
    # Fix spaces inside numbers like "575 225" -> "575225" (no separator)
    text = re.sub(r"(\d)\s+(\d{3})(?=\s|d|đ|$)", r"\1\2", text)
    return text


def _extract_supplier(lines: list[str]) -> str | None:
    """Extract supplier name by combining initial short lines that form a business name.

    EasyOCR often splits a multi-word business name across several lines
    (e.g., "DIEN" / "MAY" / "XANH"). This function merges them until it hits
    a line that looks like an address, phone, date, or separator.
    """
    stop_keywords = [
        "ngay", "ngày", "date", "hoa don", "hóa đơn", "phieu", "phiếu",
        "dt:", "đt:", "tel:", "hotline", "mst:", "sdt:", "cn:", "===", "---",
        "ban:", "bàn:", "thu ngan", "nv:", "so hd", "số hd", "ma hd", "mã hd",
    ]
    address_pattern = re.compile(
        r"\d+\s+\w+.*(?:q\.\d|quan|quận|tp\b|tphcm|ha noi|hà nội|p\.\d|phuong|phường)",
        re.IGNORECASE,
    )
    # Line starting with a street number (e.g., "168 Nguyen...", "42 Hai Ba...")
    street_number_pattern = re.compile(r"^\d{1,4}\s+[A-Z]", re.IGNORECASE)

    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        # Skip very short noise fragments (1-2 chars like "kk", "**")
        if len(stripped) <= 2 and not stripped.isalpha():
            continue
        if len(stripped) <= 2 and not parts:
            continue
        # Stop at addresses, dates, separators
        if any(kw in lower for kw in stop_keywords):
            break
        if address_pattern.search(stripped):
            break
        # Stop at lines starting with a street number (address line)
        if street_number_pattern.match(stripped):
            break
        # Stop if line looks like a phone number
        if re.match(r"^[\d\s\(\)\-\+]{7,}$", stripped):
            break
        # Stop at lines with only punctuation/stars (noise like "4**", "***")
        if re.match(r"^[\*\#\@\!\~]+$", stripped):
            continue
        parts.append(stripped)
        # A good supplier name is usually 1-3 fragments
        if len(parts) >= 4:
            break
    name = " ".join(parts).strip() if parts else (lines[0].strip() if lines else None)
    if name:
        name = re.sub(r"\s+", " ", name)
        # Strip leading OCR noise (e.g., "kk" before "THE COFFEE HOUSE")
        name = re.sub(r"^[a-z]{1,2}\s+(?=[A-Z]{2,})", "", name)
        # Strip trailing noise: punctuation-only fragments (e.g., "4**", "***")
        name = re.sub(r"\s+[\*\#\@\!\~\d]{1,4}\*+$", "", name)
    return name


def _parse_price(s: str) -> float:
    """Parse a price string like '45,000' or '45.000' into a float."""
    cleaned = s.replace(".", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _valid_item_name(name: str) -> bool:
    """Check that name contains at least one letter."""
    return bool(re.search(r"[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]", name))


def _make_item(name: str, qty: int, unit_price: float, amount: float) -> dict:
    return {
        "item_name": name,
        "quantity": qty,
        "unit_price": unit_price,
        "amount": amount,
    }


def _parse_items(lines: list[str]) -> list[dict]:
    """Parse product lines from OCR text supporting multiple Vietnamese receipt formats."""
    qty_prefix_re = re.compile(
        r"^(\d+)\s*x\s+(.+?)\s+([0-9][0-9.,]*)\s*$", re.IGNORECASE,
    )
    qty_suffix_re = re.compile(
        r"^(.+?)\s+x(\d+)\s+([0-9][0-9.,]*)\s*$", re.IGNORECASE,
    )
    numbered_re = re.compile(
        r"^(\d{1,3})\s+(.+?)\s+(\d+)\s+([0-9][0-9.,]*)\s*$",
    )
    four_col_re = re.compile(
        r"^(.+?)\s+(\d+)\s+([0-9][0-9.,]*)\s+([0-9][0-9.,]*)\s*$",
    )
    three_col_re = re.compile(
        r"^(.+?)\s+(\d+)\s+([0-9][0-9.,]*)\s*$",
    )
    sl_dg_re = re.compile(
        r"SL\s*:\s*(\d*)\s*DG\s*:\s*([0-9][0-9.,]*)", re.IGNORECASE,
    )
    two_col_re = re.compile(
        r"^(.+?)\s+([0-9][0-9.,]*)\s*$",
    )

    skip_keywords = [
        "tổng", "tong", "total", "thành tiền", "thanh tien", "thanh toan",
        "vat", "cảm ơn", "cam on", "tel", "đt:", "dt:", "địa chỉ", "dia chi",
        "hóa đơn", "hoa don", "---", "===", "hotline", "giam gia",
        "phuong thuc", "khach dua", "tien thua", "phi dich vu",
        "tam tinh", "tạm tính", "stt", "san pham", "sản phẩm",
        "nv:", "ban:", "bàn:", "thu ngan", "thủ ngân",
        "so hd", "số hd", "ma hd", "mã hd", "ngay:", "ngày:",
        "phuc vu", "phục vụ", "mst:", "phieu", "phiếu",
        "khach hang", "khách hàng", "dien thoai", "điện thoại",
        "kh:", "ds:", "sdt:", "cn:", "tt:", "ma gd",
        "bao hanh", "doi tra", "hen gap", "quy khach", "quý khách",
        "tien mat", "tiền mặt",
    ]

    items = []
    pending_name = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        check_lower = re.sub(r"\s+", " ", re.sub(r"\s*:", ":", lower))
        if any(kw in check_lower for kw in skip_keywords):
            continue
        if re.match(r"^[\*\-\=\#\+]+$", stripped):
            continue

        cleaned = stripped
        # Fix OCR misreads of quantity markers: l/I → 1
        cleaned = re.sub(r"[xX](\d+)[vV]\b", r"x\1", cleaned)
        cleaned = re.sub(r"^[IlL]x\b", "1x", cleaned)
        cleaned = re.sub(r"\b[xX][IlL]\b", "x1", cleaned)
        # Strip trailing currency suffix
        cleaned = re.sub(r"\s*(?:đ|vnd|vnđ)\s*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(\d)d\s*$", r"\1", cleaned, flags=re.IGNORECASE)

        item = None

        m = qty_prefix_re.match(cleaned)
        if m:
            qty = int(m.group(1))
            name = re.sub(r"\s+", " ", m.group(2).strip())
            amount = _parse_price(m.group(3))
            if amount > 0 and _valid_item_name(name):
                unit_price = amount / qty if qty > 0 else amount
                item = _make_item(name, qty, unit_price, amount)

        if not item:
            m = qty_suffix_re.match(cleaned)
            if m:
                name = re.sub(r"\s+", " ", m.group(1).strip())
                qty = int(m.group(2))
                amount = _parse_price(m.group(3))
                if amount > 0 and _valid_item_name(name):
                    unit_price = amount / qty if qty > 0 else amount
                    item = _make_item(name, qty, unit_price, amount)

        if not item:
            m = numbered_re.match(cleaned)
            if m:
                name = re.sub(r"\s+", " ", m.group(2).strip())
                qty = int(m.group(3))
                amount = _parse_price(m.group(4))
                if amount > 0 and _valid_item_name(name):
                    unit_price = amount / qty if qty > 0 else amount
                    item = _make_item(name, qty, unit_price, amount)

        if not item:
            m = four_col_re.match(cleaned)
            if m:
                name = re.sub(r"\s+", " ", m.group(1).strip())
                qty = int(m.group(2))
                unit_price = _parse_price(m.group(3))
                amount = _parse_price(m.group(4))
                if amount > 0 and _valid_item_name(name):
                    item = _make_item(name, qty, unit_price, amount)

        if not item:
            m = three_col_re.match(cleaned)
            if m:
                name = re.sub(r"\s+", " ", m.group(1).strip())
                qty = int(m.group(2))
                amount = _parse_price(m.group(3))
                if amount > 0 and _valid_item_name(name):
                    unit_price = amount / qty if qty > 0 else amount
                    item = _make_item(name, qty, unit_price, amount)

        if not item:
            m = sl_dg_re.search(cleaned)
            if m and pending_name:
                qty_str = m.group(1)
                qty = int(qty_str) if qty_str else 1
                amount = _parse_price(m.group(2))
                if amount > 0:
                    unit_price = amount / qty if qty > 0 else amount
                    item = _make_item(pending_name, qty, unit_price, amount)
                    pending_name = None

        if not item:
            m = two_col_re.match(cleaned)
            if m:
                name = re.sub(r"\s+", " ", m.group(1).strip())
                amount = _parse_price(m.group(2))
                if amount >= 1000 and _valid_item_name(name):
                    item = _make_item(name, 1, amount, amount)

        if item:
            items.append(item)
            pending_name = None
        elif len(stripped) >= 3 and _valid_item_name(stripped):
            pending_name = re.sub(r"\s+", " ", stripped.strip())

    return items


def parse_receipt(raw_text: str) -> dict:
    normalized = _normalize_ocr_text(raw_text)
    lines = normalized.strip().split("\n")

    supplier_name = _extract_supplier(lines)

    receipt_date = None
    date_patterns = [
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        r"Ngày[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            receipt_date = match.group(1)
            break

    # Join all lines into a single string for multi-line pattern matching
    joined = " ".join(line.strip() for line in lines if line.strip())

    total_amount = 0.0
    total_patterns = [
        # Vietnamese with diacritics
        r"(?:THÀNH TIỀN|Tổng cộng|TỔNG CỘNG|Thanh toán|THANH TOÁN|Tổng tiền)[:\s]*([0-9.,]+)\s*(?:đ|d|VND|vnđ)?",
        # Vietnamese without diacritics (OCR often strips accents)
        r"(?:THANH\s*TOAN|TONG\s*CONG|TONG\s*THANH\s*TOAN|TONG\s*TIEN)[:\s]*([0-9.,]+)\s*(?:đ|d|VND|vnđ)?",
        # "Tong tien hang:" pattern (common in electronics stores)
        r"(?:Tong\s*tien\s*hang|TONG\s*TIEN\s*HANG)[:\s]*([0-9.,]+)",
        # Amount followed by currency on same line
        r"([0-9.,]+)\s*(?:đ|VND|vnđ)\s*$",
    ]
    found_totals = []
    for pattern in total_patterns:
        # Search in both the original per-line text and the joined text
        for text_to_search in [normalized, joined]:
            for match in re.finditer(pattern, text_to_search, re.IGNORECASE | re.MULTILINE):
                amount_str = match.group(1).replace(".", "").replace(",", "")
                try:
                    val = float(amount_str)
                    if val > 0:
                        found_totals.append(val)
                except ValueError:
                    pass
    if found_totals:
        total_amount = max(found_totals)

    items = _parse_items(lines)

    return {
        "raw_text": raw_text,
        "supplier_name": supplier_name,
        "receipt_date": receipt_date,
        "total_amount": total_amount,
        "items": items,
    }

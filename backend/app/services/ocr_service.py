import re

import easyocr

reader = None


def get_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(["vi", "en"], gpu=False)
    return reader


def extract_text(image_path: str) -> str:
    r = get_reader()
    results = r.readtext(image_path, detail=0)
    return "\n".join(results)


def parse_receipt(raw_text: str) -> dict:
    lines = raw_text.strip().split("\n")

    supplier_name = lines[0].strip() if lines else None

    receipt_date = None
    date_patterns = [
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        r"Ngày[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            receipt_date = match.group(1)
            break

    total_amount = 0.0
    total_patterns = [
        r"(?:THÀNH TIỀN|Tổng cộng|Total|TỔNG|Thanh toán)[:\s]*([0-9.,]+)\s*(?:đ|VND|vnđ)?",
        r"([0-9.,]+)\s*(?:đ|VND|vnđ)\s*$",
    ]
    found_totals = []
    for pattern in total_patterns:
        for match in re.finditer(pattern, raw_text, re.IGNORECASE | re.MULTILINE):
            amount_str = match.group(1).replace(".", "").replace(",", "")
            try:
                found_totals.append(float(amount_str))
            except ValueError:
                pass
    if found_totals:
        total_amount = max(found_totals)

    items = []
    item_pattern = re.compile(
        r"^(.+?)\s+(\d+)\s+x?\s*([0-9.,]+)\s*$", re.IGNORECASE
    )
    price_pattern = re.compile(
        r"^(.+?)\s+(\d+)\s+([0-9.,]+)\s+([0-9.,]+)\s*$"
    )

    for line in lines:
        line = line.strip()
        if not line or any(
            kw in line.lower()
            for kw in ["tổng", "total", "thành tiền", "vat", "cảm ơn", "tel", "đt:", "địa chỉ", "hóa đơn số", "---", "==="]
        ):
            continue

        m = price_pattern.match(line)
        if m:
            name = m.group(1).strip()
            qty = int(m.group(2))
            unit_price_str = m.group(3).replace(".", "").replace(",", "")
            amount_str = m.group(4).replace(".", "").replace(",", "")
            try:
                unit_price = float(unit_price_str)
                amount = float(amount_str)
            except ValueError:
                continue
            items.append({
                "item_name": name,
                "quantity": qty,
                "unit_price": unit_price,
                "amount": amount,
            })
            continue

        m = item_pattern.match(line)
        if m:
            name = m.group(1).strip()
            qty = int(m.group(2))
            price_str = m.group(3).replace(".", "").replace(",", "")
            try:
                unit_price = float(price_str)
            except ValueError:
                continue
            items.append({
                "item_name": name,
                "quantity": qty,
                "unit_price": unit_price,
                "amount": unit_price * qty,
            })

    return {
        "raw_text": raw_text,
        "supplier_name": supplier_name,
        "receipt_date": receipt_date,
        "total_amount": total_amount,
        "items": items,
    }

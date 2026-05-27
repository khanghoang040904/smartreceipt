from __future__ import annotations

import logging
import re
import unicodedata

import easyocr

from app.services.gemini_service import is_gemini_available, parse_receipt_image, parse_receipt_text

logger = logging.getLogger(__name__)

reader = None


TOTAL_KEYWORDS = [
    "TONG",
    "TONG CONG",
    "TONG TIEN",
    "TONG TIEN HANG",
    "THANH TOAN",
    "THANH TIEN",
    "TOTAL",
    "AMOUNT",
    "PAYMENT",
]

SUPPLIER_STOP_KEYWORDS = [
    "DIA CHI",
    "HOA DON",
    "PHIEU",
    "NGAY",
    "SO HD",
    "MA HD",
    "MST",
    "TEL",
    "HOTLINE",
    "SDT",
    "DT:",
    "CN:",
    "BAN:",
    "NV:",
    "KH:",
    "THU NGAN",
    "TONG",
    "TOTAL",
]

ITEM_SKIP_KEYWORDS = [
    "TONG",
    "TOTAL",
    "THANH TOAN",
    "THANH TIEN",
    "VAT",
    "GIAM GIA",
    "TIEN HANG",
    "KHACH DUA",
    "TIEN THUA",
    "CAM ON",
    "NGAY",
    "GIO",
    "TEL",
    "HOTLINE",
    "SDT",
    "DT:",
    "DIA CHI",
    "HOA DON",
    "PHIEU",
    "MST",
    "HD:",
    "MA HD",
    "MA GD",
    "SO HD",
    "THU NGAN",
    "DUOC SI",
    "DS:",
    "NHAN VIEN",
    "KHACH HANG",
    "---",
    "===",
]

ITEM_UNITS = [
    "CAI",
    "CHAI",
    "GOI",
    "HOP",
    "KG",
    "G",
    "GRAM",
    "ML",
    "MG",
    "L",
    "LY",
    "SUAT",
    "PHAN",
    "VI",
    "TUI",
    "LON",
    "VIEN",
    "QUA",
    "HOP",
]


def get_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(["vi", "en"], gpu=False)
    return reader


def extract_text(image_path: str) -> str:
    r = get_reader()
    results = r.readtext(image_path, detail=0)
    return "\n".join(results)


def process_receipt(image_path: str) -> dict:
    """Extract and parse receipt using Gemini Vision if available, else EasyOCR + regex."""
    if is_gemini_available():
        gemini_result = parse_receipt_image(image_path)
        if gemini_result and _is_valid_gemini_result(gemini_result):
            raw_text = extract_text(image_path)
            gemini_result["raw_text"] = raw_text
            logger.info("Receipt parsed via Gemini Vision")
            return gemini_result

    raw_text = extract_text(image_path)

    if is_gemini_available():
        gemini_result = parse_receipt_text(raw_text)
        if gemini_result and _is_valid_gemini_result(gemini_result):
            gemini_result["raw_text"] = raw_text
            logger.info("Receipt parsed via Gemini text")
            return gemini_result

    logger.info("Receipt parsed via regex fallback")
    return parse_receipt(raw_text)


def _is_valid_gemini_result(result: dict) -> bool:
    if result.get("supplier_name") or result.get("total_amount"):
        return True
    if result.get("items"):
        return True
    return False


def parse_receipt(raw_text: str) -> dict:
    lines = _normalize_ocr_lines(raw_text)
    normalized_text = "\n".join(lines)

    return {
        "raw_text": normalized_text,
        "supplier_name": _extract_supplier(lines),
        "receipt_date": _extract_date(normalized_text),
        "total_amount": _extract_total(lines, raw_text),
        "items": _extract_items(lines),
    }


def _normalize_ocr_lines(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in normalized.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        line = re.sub(r"(?<=\d)[oO](?=\d)", "0", line)
        line = re.sub(r"(?<=\d)\s*([,.])\s*(?=\d)", r"\1", line)
        line = re.sub(r"(?<=\d)\s+(?=\d{3}(?:\D|$))", "", line)
        if line:
            lines.append(line)
    return lines


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("Đ", "D").replace("đ", "d")
    text = re.sub(r"\s+", " ", text)
    return text.upper().strip()


def _clean_supplier(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" -:*#")
    return text or None


def _is_noise_header(line: str) -> bool:
    folded = _fold(line)
    alpha_count = sum(ch.isalpha() for ch in folded)
    if alpha_count < 2:
        return True
    if len(line.strip()) <= 3 and line.strip().islower():
        return True
    return False


def _is_supplier_fragment(line: str) -> bool:
    folded = _fold(line)
    if _is_noise_header(line):
        return False
    if any(keyword in folded for keyword in SUPPLIER_STOP_KEYWORDS):
        return False
    if re.search(r"\d", folded):
        return False
    letters = [ch for ch in folded if ch.isalpha()]
    if not letters:
        return False
    return True


def _extract_supplier(lines: list[str]) -> str | None:
    fragments = []
    for line in lines[:12]:
        if not fragments and not _is_supplier_fragment(line):
            continue
        if fragments and not _is_supplier_fragment(line):
            break
        fragments.append(line)
        if len(fragments) >= 4:
            break

    if fragments:
        return _clean_supplier(" ".join(fragments))
    return _clean_supplier(lines[0]) if lines else None


def _extract_date(text: str) -> str | None:
    patterns = [
        r"(?:NGAY|DATE)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    ]
    folded_text = _fold(text)
    for pattern in patterns:
        match = re.search(pattern, folded_text, re.IGNORECASE)
        if match:
            return match.group(1)
    vietnamese_date = re.search(
        r"NGAY\s+(\d{1,2})\s+THANG\s+(\d{1,2})\s+NAM\s+(\d{4})",
        folded_text,
        re.IGNORECASE,
    )
    if vietnamese_date:
        day, month, year = vietnamese_date.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"
    return None


def _extract_amounts(text: str) -> list[float]:
    amounts = []
    patterns = [
        r"(?<!\d)(\d{1,3}(?:\s*[,.]\s*\d{3})+|\d{1,3}(?:\s+\d{3})+|\d{4,})(?:\s*(?:d|đ|vnd|vnđ))?(?!\d)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            digits = re.sub(r"\D", "", match.group(1))
            if len(digits) < 4:
                continue
            try:
                amounts.append(float(digits))
            except ValueError:
                continue
    return amounts


def _extract_total(lines: list[str], original_text: str) -> float:
    candidates: list[tuple[int, float]] = []
    folded_lines = [_fold(line) for line in lines]

    for index, folded_line in enumerate(folded_lines):
        if not _starts_total_window(folded_line):
            continue
        if ("HOA DON" in folded_line or "PHIEU" in folded_line) and "TONG" not in folded_line:
            continue
        folded_window = " ".join(folded_lines[index:index + 4])
        if not any(keyword in folded_window for keyword in TOTAL_KEYWORDS):
            continue

        window = " ".join(lines[index:index + 5])
        amounts = _extract_amounts(window)
        score = 3
        if "THANH TOAN" in folded_window or "THANH TIEN" in folded_window:
            score = 4
        if "TAM TINH" in folded_window:
            score = 1
        for amount in amounts[:1]:
            candidates.append((score, amount))

    legacy_patterns = [
        r"(?:THÀNH TIỀN|TỔNG CỘNG|TỔNG|THANH TOÁN|TOTAL)[:\s]*([0-9.,\s]+)\s*(?:VND|VNĐ|d|đ)?",
        r"([0-9.,\s]+)\s*(?:VND|VNĐ|d|đ)\s*$",
    ]
    for pattern in legacy_patterns:
        for match in re.finditer(pattern, original_text, re.IGNORECASE | re.MULTILINE):
            for amount in _extract_amounts(match.group(1)):
                candidates.append((2, amount))

    if not candidates:
        return 0.0

    max_amount = max(amount for _, amount in candidates)
    best_score = max(score for score, _ in candidates)
    best_score_amount = max(amount for score, amount in candidates if score == best_score)
    if best_score >= 4 and best_score_amount >= max_amount * 0.7:
        return best_score_amount
    return max_amount


def _starts_total_window(folded_line: str) -> bool:
    return any(
        marker in folded_line
        for marker in ["TONG", "THANH", "TOTAL", "AMOUNT", "PAYMENT"]
    )


def _should_skip_item_line(line: str) -> bool:
    folded = _fold(line)
    for keyword in ITEM_SKIP_KEYWORDS:
        if keyword in {"TONG", "TOTAL"}:
            if folded.startswith(keyword):
                return True
            continue
        if keyword in folded:
            return True
    if re.search(r"(?:\+?84|0)\d{2,}\s*\d{3,}", folded):
        return True
    if re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}", folded):
        return True
    if re.search(r"\b\d{1,2}:\d{2}\b", folded):
        return True
    if re.fullmatch(r"[A-Z]{2,6}\s*[-:]?\s*\d{4}", folded):
        return True
    if re.fullmatch(r"[A-Z]{2,6}\s*[-:]?\s*\d{2,4}\s*[-:]\s*\d+", folded):
        return True
    return False


def _extract_items(lines: list[str]) -> list[dict]:
    items = []
    fragments: list[str] = []

    for line in lines:
        if _should_skip_item_line(line):
            if items and _starts_total_window(_fold(line)):
                break
            fragments = []
            continue

        if _is_amount_only_line(line):
            item = _build_item_from_parts(" ".join(fragments), line)
            if item:
                items.append(item)
            fragments = []
            continue

        item = _extract_item_from_single_line(line)
        if item:
            items.append(item)
            fragments = []
            continue

        if fragments and _looks_like_quantity_fragment(line):
            fragments.append(line)
            continue

        if _looks_like_item_fragment(line):
            fragments.append(line)
            if len(fragments) > 8:
                fragments = fragments[-8:]
        else:
            fragments = []

    return items


def _is_amount_only_line(line: str) -> bool:
    if _should_skip_item_line(line):
        return False
    stripped = line.strip()
    return bool(re.fullmatch(r"(?:[0-9][0-9.,\s]*)(?:\s*(?:d|đ|vnd|vnđ))?", stripped, re.IGNORECASE)) and bool(_extract_amounts(line))


def _looks_like_item_fragment(line: str) -> bool:
    folded = _fold(line)
    if not folded or _should_skip_item_line(line):
        return False
    if re.fullmatch(r"[-=_* .]+", line):
        return False
    if re.fullmatch(r"X\s*\d+", folded):
        return True
    alpha_count = sum(ch.isalpha() for ch in folded)
    if alpha_count < 2:
        return False
    if re.search(r"\d", folded):
        unit_pattern = "|".join(ITEM_UNITS)
        has_item_unit = re.search(rf"\d+\s*(?:{unit_pattern})\b", folded) or re.search(r"\bX\s*\d+\b", folded)
        has_text = alpha_count >= 2 and not re.fullmatch(r"[A-Z]{1,3}[-:\s]*\d+", folded)
        if not has_item_unit and not has_text:
            return False
    return True


def _looks_like_quantity_fragment(line: str) -> bool:
    folded = _fold(line)
    unit_pattern = "|".join(ITEM_UNITS)
    return bool(
        re.fullmatch(rf"(?:X\s*)?\d+\s*(?:{unit_pattern})?", folded)
    )


def _extract_item_from_single_line(line: str) -> dict | None:
    if _should_skip_item_line(line):
        return None

    amount_token = r"(\d{1,3}(?:[,.]\d{3})+|\d{1,3}(?:\s+\d{3})+|\d{4,})(?:\s*(?:d|đ|vnd|vnđ))?"
    two_amount_match = re.match(
        rf"^(.+?)\s+(?:x|sl:?\s*)?(\d+)\s+{amount_token}\s+{amount_token}\s*$",
        line,
        re.IGNORECASE,
    )
    if two_amount_match:
        name, qty_text, unit_text, amount_text = two_amount_match.groups()
        return _build_item(name, qty_text, unit_text, amount_text)

    x_amount_match = re.match(rf"^(.+?)\s+x\s*(\d+)\s+{amount_token}\s*$", line, re.IGNORECASE)
    if x_amount_match:
        name, qty_text, unit_text = x_amount_match.groups()
        return _build_item(name, qty_text, unit_text, None)

    qty_amount_match = re.match(rf"^(.+?)\s+(?:sl:?\s*)?(\d+)\s+{amount_token}\s*$", line, re.IGNORECASE)
    if qty_amount_match:
        name, qty_text, unit_text = qty_amount_match.groups()
        if len(re.sub(r"\D", "", unit_text)) >= 4:
            return _build_item(name, qty_text, unit_text, None)

    prefix_unit = "|".join(ITEM_UNITS)
    prefix_match = re.match(
        rf"^(\d+)\s*(?:{prefix_unit})?\s+(.+?)\s+{amount_token}\s*$",
        _fold(line),
        re.IGNORECASE,
    )
    if prefix_match:
        qty_text, folded_name, unit_text = prefix_match.groups()
        original_name = _remove_trailing_amount(line)
        original_name = re.sub(rf"^\s*\d+\s*(?:{prefix_unit})?\s+", "", original_name, flags=re.IGNORECASE)
        return _build_item(original_name or folded_name, qty_text, unit_text, None)

    trailing_amount = re.match(rf"^(.+?)\s+{amount_token}\s*$", line, re.IGNORECASE)
    if trailing_amount:
        name, unit_text = trailing_amount.groups()
        name, qty = _extract_quantity_from_name(name)
        return _build_item(name, str(qty), unit_text, None)

    return None


def _build_item_from_parts(name: str, amount_text: str) -> dict | None:
    if not name:
        return None
    name, qty = _extract_quantity_from_name(name)
    return _build_item(name, str(qty), amount_text, None)


def _extract_quantity_from_name(name: str) -> tuple[str, int]:
    qty = 1
    x_match = re.search(r"\b[xX]\s*(\d+)\b", name)
    if x_match:
        qty = int(x_match.group(1))
        name = (name[:x_match.start()] + name[x_match.end():]).strip()

    unit_pattern = "|".join(ITEM_UNITS)
    prefix_match = re.match(rf"^\s*(\d+)\s*(?:{unit_pattern})\s+(.+)$", _fold(name), re.IGNORECASE)
    if prefix_match:
        qty = int(prefix_match.group(1))
        name = re.sub(rf"^\s*\d+\s*\w+\s+", "", name, count=1, flags=re.IGNORECASE).strip()

    return name, qty


def _remove_trailing_amount(line: str) -> str:
    return re.sub(
        r"\s+\d{1,3}(?:[,.]\d{3})+(?:\s*(?:d|đ|vnd|vnđ))?\s*$|\s+\d{4,}(?:\s*(?:d|đ|vnd|vnđ))?\s*$",
        "",
        line,
        flags=re.IGNORECASE,
    ).strip()


def _build_item(
    name: str,
    qty_text: str,
    unit_price_text: str,
    amount_text: str | None,
) -> dict | None:
    name = re.sub(r"\s+", " ", name).strip(" -:")
    if len(name) < 3 or _should_skip_item_line(name):
        return None
    try:
        qty = int(qty_text)
        first_amount = _extract_amounts(unit_price_text)[0]
        if amount_text:
            unit_price = first_amount
            amount = _extract_amounts(amount_text)[0]
        else:
            amount = first_amount
            unit_price = amount / qty if qty > 1 else amount
    except (ValueError, IndexError):
        return None
    if qty <= 0 or unit_price <= 0 or amount <= 0:
        return None
    return {
        "item_name": name,
        "quantity": qty,
        "unit_price": unit_price,
        "amount": amount,
    }

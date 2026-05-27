from __future__ import annotations

import logging
import mimetypes

import easyocr

from app.services.gemini_service import parse_receipt_image, parse_receipt_text

logger = logging.getLogger(__name__)

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


def process_receipt(image_path: str) -> dict:
    """Extract and parse receipt using Gemini Vision, then Gemini Text fallback."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

    gemini_result = parse_receipt_image(image_path, mime_type)
    if gemini_result and _is_valid_gemini_result(gemini_result):
        raw_text = extract_text(image_path)
        gemini_result["raw_text"] = raw_text
        logger.info("Receipt parsed via Gemini Vision")
        return gemini_result

    raw_text = extract_text(image_path)

    gemini_result = parse_receipt_text(raw_text)
    if gemini_result and _is_valid_gemini_result(gemini_result):
        gemini_result["raw_text"] = raw_text
        logger.info("Receipt parsed via Gemini text")
        return gemini_result

    logger.warning("Both Gemini Vision and Text failed; returning raw text only")
    return {
        "raw_text": raw_text,
        "supplier_name": None,
        "receipt_date": None,
        "total_amount": 0.0,
        "items": [],
    }


def _is_valid_gemini_result(result: dict) -> bool:
    if result.get("supplier_name") or result.get("total_amount"):
        return True
    if result.get("items"):
        return True
    return False

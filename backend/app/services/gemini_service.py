from __future__ import annotations

import json
import logging
import re

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

_client: genai.Client | None = None
_logged_no_key = False


def _get_client() -> genai.Client | None:
    global _client, _logged_no_key
    if not GEMINI_API_KEY:
        if not _logged_no_key:
            logger.warning("GEMINI_API_KEY not set — Gemini features disabled")
            _logged_no_key = True
        return None
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client initialized with model=%s", GEMINI_MODEL)
    return _client


def parse_receipt_image(image_path: str, mime_type: str = "image/png") -> dict | None:
    """Use Gemini Vision to parse a receipt image into structured data."""
    client = _get_client()
    if client is None:
        return None

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = """Phân tích hình ảnh hóa đơn/receipt này và trích xuất thông tin theo format JSON.
Trả về ĐÚNG JSON (không markdown, không ```json```) với cấu trúc:
{
  "supplier_name": "tên cửa hàng/nhà cung cấp",
  "receipt_date": "dd/mm/yyyy",
  "total_amount": 0,
  "note": "ghi chú thêm: VAT, giảm giá, ...",
  "items": [
    {
      "item_name": "tên sản phẩm bằng tiếng Việt có dấu",
      "quantity": 1,
      "unit_price": 0,
      "amount": 0
    }
  ]
}

Quy tắc:
- supplier_name: Tên cửa hàng/quán/nhà thuốc ở đầu hóa đơn. Giữ nguyên tên gốc.
- receipt_date: Ngày trên hóa đơn, format dd/mm/yyyy. Null nếu không tìm thấy.
- total_amount: Tổng tiền cuối cùng phải thanh toán (VND). Số nguyên, không có dấu chấm phân cách.
- note: Ghi chú thêm về hóa đơn, ví dụ: VAT, giảm giá, phương thức thanh toán, v.v. Null nếu không có.
- items: Danh sách sản phẩm/món. Mỗi item có tên, số lượng, đơn giá, thành tiền.
- item_name: PHẢI viết bằng tiếng Việt CÓ DẤU đầy đủ (ví dụ: "Cà phê sữa đá" không phải "Ca phe sua da").
- Tất cả giá trị tiền là số nguyên (VND), không dấu chấm, không dấu phẩy.
- Nếu không tìm thấy thông tin nào, để null hoặc 0.
- CHỈ trả về JSON, không có text khác."""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ],
        )

        return _parse_json_response(response.text)
    except Exception:
        logger.exception("Gemini Vision parsing failed")
        return None


def parse_receipt_text(raw_text: str) -> dict | None:
    """Use Gemini to parse OCR text into structured receipt data."""
    client = _get_client()
    if client is None:
        return None

    try:
        prompt = f"""Đây là text được trích xuất từ hóa đơn bằng OCR. Hãy phân tích và trả về JSON.
Trả về ĐÚNG JSON (không markdown, không ```json```) với cấu trúc:
{{
  "supplier_name": "tên cửa hàng/nhà cung cấp",
  "receipt_date": "dd/mm/yyyy",
  "total_amount": 0,
  "note": "ghi chú thêm: VAT, giảm giá, ...",
  "items": [
    {{
      "item_name": "tên sản phẩm bằng tiếng Việt có dấu",
      "quantity": 1,
      "unit_price": 0,
      "amount": 0
    }}
  ]
}}

Quy tắc:
- supplier_name: Tên cửa hàng/quán/nhà thuốc. Giữ nguyên tên gốc.
- receipt_date: Format dd/mm/yyyy. Null nếu không tìm thấy.
- total_amount: Tổng tiền cuối cùng (VND). Số nguyên.
- note: Ghi chú thêm: VAT, giảm giá, phương thức thanh toán, v.v. Null nếu không có.
- items: Danh sách sản phẩm. Mỗi item có tên, số lượng, đơn giá, thành tiền.
- item_name: PHẢI viết bằng tiếng Việt CÓ DẤU đầy đủ.
- Tất cả giá trị tiền là số nguyên (VND).
- CHỈ trả về JSON, không có text khác.

OCR Text:
{raw_text}"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        return _parse_json_response(response.text)
    except Exception:
        logger.exception("Gemini text parsing failed")
        return None


def chat_with_context(
    user_message: str,
    receipt_context: str,
) -> str | None:
    """Use Gemini to answer questions about receipts with RAG context."""
    client = _get_client()
    if client is None:
        return None

    try:
        system_prompt = """Bạn là trợ lý thông minh cho ứng dụng quản lý hóa đơn SmartReceipt.
Nhiệm vụ: Trả lời câu hỏi của người dùng về hóa đơn, chi tiêu, sản phẩm dựa trên dữ liệu được cung cấp.

Quy tắc:
- Trả lời bằng tiếng Việt, ngắn gọn, chính xác.
- Chỉ dựa trên dữ liệu hóa đơn được cung cấp. Không bịa thông tin.
- Khi nói về tiền, format: X đ (ví dụ: 150.000 đ). Dùng dấu chấm phân cách hàng nghìn.
- Nếu không đủ dữ liệu, nói rõ là không tìm thấy.
- Có thể tính tổng, so sánh, tìm kiếm sản phẩm, phân tích chi tiêu.
- Nếu người dùng hỏi chung chung, tóm tắt thông tin có sẵn."""

        contents = f"""Dữ liệu hóa đơn liên quan:
{receipt_context}

Câu hỏi của người dùng: {user_message}"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )

        return response.text.strip() if response.text else None
    except Exception:
        logger.exception("Gemini chat failed")
        return None


def _parse_json_response(text: str) -> dict | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse Gemini JSON response: %s", text[:200])
                return None
        else:
            return None

    result = {
        "supplier_name": data.get("supplier_name"),
        "receipt_date": data.get("receipt_date"),
        "total_amount": _safe_float(data.get("total_amount", 0)),
        "note": data.get("note"),
        "items": [],
    }

    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        name = item.get("item_name", "").strip()
        if not name:
            continue
        result["items"].append({
            "item_name": name,
            "quantity": int(item.get("quantity", 1) or 1),
            "unit_price": _safe_float(item.get("unit_price", 0)),
            "amount": _safe_float(item.get("amount", 0)),
        })

    return result


def _safe_float(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    return 0.0

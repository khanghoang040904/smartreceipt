from unittest.mock import patch

from app.services.gemini_service import _parse_json_response


SAMPLE_GEMINI_RESPONSE = """{
  "supplier_name": "SIÊU THỊ COOP MART",
  "receipt_date": "12/12/2024",
  "total_amount": 805200,
  "items": [
    {"item_name": "Gạo ST25 (5kg)", "quantity": 1, "unit_price": 189000, "amount": 189000},
    {"item_name": "Nước mắm Phú Quốc", "quantity": 2, "unit_price": 45000, "amount": 90000}
  ]
}"""


def test_parse_json_response_supplier_name():
    result = _parse_json_response(SAMPLE_GEMINI_RESPONSE)
    assert result["supplier_name"] == "SIÊU THỊ COOP MART"


def test_parse_json_response_date():
    result = _parse_json_response(SAMPLE_GEMINI_RESPONSE)
    assert result["receipt_date"] == "12/12/2024"


def test_parse_json_response_total_amount():
    result = _parse_json_response(SAMPLE_GEMINI_RESPONSE)
    assert result["total_amount"] == 805200.0


def test_parse_json_response_handles_markdown_wrapper():
    wrapped = "```json\n" + SAMPLE_GEMINI_RESPONSE + "\n```"
    result = _parse_json_response(wrapped)
    assert result["supplier_name"] == "SIÊU THỊ COOP MART"
    assert result["total_amount"] == 805200.0


def test_parse_json_response_returns_none_for_invalid():
    assert _parse_json_response("not json at all") is None
    assert _parse_json_response("") is None
    assert _parse_json_response(None) is None

from app.services.ocr_service import parse_receipt


SAMPLE_TEXT = """SIÊU THỊ COOP MART
274 Cộng Hòa, Phường 13, Tân Bình, TP.HCM
Tel: (028) 3948 8888
==============================
Ngày: 12/12/2024   Giờ: 14:32
Hóa đơn số: INV-20241212-0087
------------------------------
Gạo ST25 (5kg)        1  189000
Nước mắm Phú Quốc     2  45000
------------------------------
Tổng cộng:          732,000
THÀNH TIỀN:         805,200đ
------------------------------
Cảm ơn quý khách!"""


# TC13: Parse supplier name from OCR text
def test_parse_supplier_name():
    result = parse_receipt(SAMPLE_TEXT)
    assert result["supplier_name"] == "SIÊU THỊ COOP MART"


# TC14: Parse date from OCR text
def test_parse_date():
    result = parse_receipt(SAMPLE_TEXT)
    assert result["receipt_date"] == "12/12/2024"


# TC15: Parse total amount from OCR text
def test_parse_total_amount():
    result = parse_receipt(SAMPLE_TEXT)
    assert result["total_amount"] == 805200.0

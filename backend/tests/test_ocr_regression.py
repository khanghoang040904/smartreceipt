from pathlib import Path

from app.services.ocr_service import parse_receipt


TEST_IMAGE_DIR = Path(__file__).resolve().parents[2].parent / "Test"


OCR_CASES = [
    {
        "image": "receipt_coffeeshop.png",
        "supplier": "THE COFFEE HOUSE",
        "date": "12/05/2025",
        "total": 216000.0,
        "items": [
            ("Cà phê sữa đá", 2, 45000.0),
            ("Trà đào cam sả", 1, 58000.0),
            ("Bánh mì que", 1, 68000.0),
        ],
        "text": """THE COFFEE HOUSE
42 Hai Bà Trưng, Quận 1, TPHCM
Hotline: 1900 6009
HÓA ĐƠN THANH TOÁN
Số HD: TCH-20250512-1234
Ngày: 12/05/2025 09:15
------------------------------
Cà phê sữa đá x2 90,000đ
Trà đào cam sả 58,000đ
Bánh mì que 68,000đ
Tổng Cộng
216,000đ""",
    },
    {
        "image": "receipt_electronics.png",
        "supplier": "DIEN MAY XANH",
        "date": "08/05/2025",
        "total": 8760000.0,
        "items": [
            ("Máy lọc không khí", 1, 4500000.0),
            ("Nồi chiên không dầu", 1, 2990000.0),
            ("Bảo hành mở rộng", 1, 1270000.0),
        ],
        "text": """DIEN
MAY
XANH
CN: 256 Lê Hồng Phong, Q.10
Ngày: 08/05/2025
------------------------------
Máy lọc không khí 4,500,000
Nồi chiên không dầu 2,990,000
Bảo hành mở rộng 1,270,000
Tổng
tiền
hàng:
8,760,000
Giảm giá KM:
500,000
THANH TOÁN:
260,000 VND""",
    },
    {
        "image": "receipt_supermarket.png",
        "supplier": "SIEU THI CO. OPMART",
        "date": "10/05/2025",
        "total": 575225.0,
        "items": [
            ("Gạo ST25 5kg", 1, 189000.0),
            ("Sữa tươi Vinamilk", 2, 37000.0),
            ("Trứng gà hộp 10 quả", 1, 42000.0),
            ("Nước mắm Phú Quốc", 1, 78000.0),
            ("Rau củ tổng hợp", 1, 192225.0),
        ],
        "text": """SIEU THI CO. OPMART
168 Nguyễn Đình Chiểu, Quận 3
HÓA ĐƠN BÁN HÀNG
Ngày: 10/05/2025
Gạo ST25 5kg 189,000đ
Sữa tươi Vinamilk x2 74,000đ
Trứng gà hộp 10 quả 42,000đ
Nước mắm Phú Quốc 78,000đ
Rau củ tổng hợp 192,225đ
Tổng
cộng
(8 SP)
605,500đ
Giảm giá thẻ VIP 5%:
30,275đ
THANH
TOÁN:
575,225đ""",
    },
    {
        "image": "receipt_pharmacy.png",
        "supplier": "NHA THUOC AN KHANG",
        "date": "09/05/2025",
        "total": 220000.0,
        "items": [
            ("Paracetamol 500mg", 2, 35000.0),
            ("Vitamin C 1000mg", 1, 85000.0),
            ("Nước muối sinh lý", 5, 13000.0),
        ],
        "text": """NHA THUOC
AN KHANG
78 Nguyễn Thị Minh Khai
ĐT: 028 3822 1100
Ngày 09/05/2025
Paracetamol 500mg x2
70,000
Vitamin C 1000mg
85,000
Nước muối sinh lý x5
65,000
Tổng Cộng
220,000 VND""",
    },
    {
        "image": "receipt_restaurant.png",
        "supplier": "NHA HANG HAI SAN BIEN DONG",
        "date": "11/05/25",
        "total": 1197800.0,
        "items": [
            ("Tôm hùm nướng", 1, 650000.0),
            ("Mực hấp gừng", 1, 210000.0),
            ("Cơm chiên hải sản", 1, 120000.0),
            ("Nước suối", 4, 20000.0),
        ],
        "text": """NHA
HANG HAI SAN BIEN DONG
55 Võ Văn Kiệt
Tel: 028-3821-5566
Ngày 11/05/25
Tôm hùm nướng 650,000
Mực hấp gừng 210,000
Cơm chiên hải sản 120,000
Nước suối x4 80,000
Tổng:
1,060,000
Phí dịch vụ 5%:
53,000
VAT 8%:
84,800
Tổng THANH TOÁN: 1,197,800đ""",
    },
    {
        "image": "receipt_camera_style.png",
        "supplier": "BACH HOA XANH",
        "date": "13/05/2025",
        "total": 531000.0,
        "items": [
            ("Bò Úc nhập khẩu 500g", 1, 185000.0),
            ("Cá hồi Na Uy 300g", 1, 165000.0),
            ("Rau xà lách (gói)", 1, 25000.0),
            ("Cà chua (kg)", 1, 32000.0),
            ("Hành tây (kg)", 1, 28000.0),
            ("Sữa chua Vinamilk", 4, 9000.0),
            ("Bánh mì sandwich", 1, 22000.0),
            ("Nước suối Lavie 6L", 1, 38000.0),
        ],
        "text": """BACH HOA XANH
99 Phan Xích Long, Phú Nhuận
TPHCM - MST: 0316657398
HD: BHX-20250513-7720
Ngày: 13/05/2025 18:22
==============================
Bò Úc nhập khẩu 500g
185,000
Cá hồi Na Uy 300g
165,000
Rau xà lách (gói)
25,000
Cà chua (kg)
32,000
Hành tây (kg)
28,000
Sữa chua Vinamilk x4
36,000
Bánh mì sandwich
22,000
Nước suối Lavie 6L
38,000
==============================
Tổng Cộng
531,000 VND""",
    },
    {
        "image": "receipt_vietnamese_grocery.png",
        "supplier": "CỬA HÀNG THỰC PHẨM MINH AN",
        "date": "14/05/2025",
        "total": 312000.0,
        "items": [
            ("Thịt heo ba rọi 500g", 1, 98000.0),
            ("Cà chua Đà Lạt 1kg", 1, 32000.0),
            ("Rau muống bó", 2, 12000.0),
            ("Nước mắm Nam Ngư", 2, 43000.0),
            ("Trứng gà hộp 10 quả", 1, 72000.0),
        ],
        "text": """CỬA HÀNG THỰC PHẨM MINH AN
12 Lý Thường Kiệt, Quận Tân Bình
Ngày: 14/05/2025
Thịt heo ba rọi 500g 98,000đ
Cà chua Đà Lạt 1kg 32,000đ
Rau muống bó x2 24,000đ
Nước mắm Nam Ngư x2
86,000đ
Trứng gà hộp 10 quả
72,000đ
THÀNH
TOÁN
312,000đ""",
    },
    {
        "image": "receipt_vietnamese_cafe.png",
        "supplier": "CÀ PHÊ HOA NẮNG",
        "date": "15/05/2025",
        "total": 154000.0,
        "items": [
            ("Cà phê sữa đá", 2, 29000.0),
            ("Bạc xỉu nóng", 1, 36000.0),
            ("Bánh croissant bơ", 2, 30000.0),
        ],
        "text": """CÀ PHÊ HOA NẮNG
88 Nguyễn Huệ, Quận 1
Ngày 15/05/2025
Cà phê sữa đá x2
58,000
Bạc xỉu nóng
36,000
Bánh croissant bơ x2
60,000
Tổng thanh toán: 154,000đ""",
    },
    {
        "image": "receipt_vietnamese_pharmacy.png",
        "supplier": "NHÀ THUỐC TÂM ĐỨC",
        "date": "16/05/2025",
        "total": 286000.0,
        "items": [
            ("Khẩu trang y tế hộp", 2, 45000.0),
            ("Siro ho Prospan", 1, 126000.0),
            ("Nước muối sinh lý", 5, 14000.0),
        ],
        "text": """NHÀ THUỐC TÂM ĐỨC
25 Trần Hưng Đạo, Quận 5
SĐT: 028 3999 8888
Ngày: 16/05/2025
Khẩu trang y tế hộp x2 90,000
Siro ho Prospan 126,000
Nước muối sinh lý x5 70,000
VAT 0%
Tổng tiền thanh toán
286,000 VND""",
    },
]


def test_test_receipt_images_exist():
    missing = [case["image"] for case in OCR_CASES if not (TEST_IMAGE_DIR / case["image"]).exists()]
    assert missing == []


def test_parse_all_receipt_regression_cases():
    for case in OCR_CASES:
        parsed = parse_receipt(case["text"])
        assert parsed["supplier_name"] == case["supplier"], case["image"]
        assert parsed["receipt_date"] == case["date"], case["image"]
        assert parsed["total_amount"] == case["total"], case["image"]


def test_parse_vietnamese_item_regression_cases():
    for case in OCR_CASES:
        parsed = parse_receipt(case["text"])
        items = parsed["items"]
        expected_items = case["items"]
        assert len(items) == len(expected_items), case["image"]
        for item, expected in zip(items, expected_items):
            name, quantity, unit_price = expected
            assert item["item_name"] == name, case["image"]
            assert item["quantity"] == quantity, case["image"]
            assert item["unit_price"] == unit_price, case["image"]

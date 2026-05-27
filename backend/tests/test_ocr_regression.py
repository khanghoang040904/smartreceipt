import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.gemini_service import _parse_json_response


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
    },
]


def _make_gemini_json(case: dict) -> str:
    items = [
        {
            "item_name": name,
            "quantity": qty,
            "unit_price": price,
            "amount": price * qty,
        }
        for name, qty, price in case["items"]
    ]
    return json.dumps({
        "supplier_name": case["supplier"],
        "receipt_date": case["date"],
        "total_amount": case["total"],
        "items": items,
    })


@pytest.mark.skipif(not TEST_IMAGE_DIR.exists(), reason="Test images directory not available")
def test_test_receipt_images_exist():
    missing = [case["image"] for case in OCR_CASES if not (TEST_IMAGE_DIR / case["image"]).exists()]
    assert missing == []


def test_parse_json_response_all_cases():
    for case in OCR_CASES:
        gemini_json = _make_gemini_json(case)
        parsed = _parse_json_response(gemini_json)
        assert parsed is not None, case["image"]
        assert parsed["supplier_name"] == case["supplier"], case["image"]
        assert parsed["receipt_date"] == case["date"], case["image"]
        assert parsed["total_amount"] == case["total"], case["image"]


def test_parse_json_response_items():
    for case in OCR_CASES:
        gemini_json = _make_gemini_json(case)
        parsed = _parse_json_response(gemini_json)
        items = parsed["items"]
        expected_items = case["items"]
        assert len(items) == len(expected_items), case["image"]
        for item, expected in zip(items, expected_items):
            name, quantity, unit_price = expected
            assert item["item_name"] == name, case["image"]
            assert item["quantity"] == quantity, case["image"]
            assert item["unit_price"] == unit_price, case["image"]

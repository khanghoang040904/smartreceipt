from app.models.receipt import Receipt, ReceiptItem
from app.services.receipt_index_service import build_receipt_chunks, normalize_for_search


def test_build_receipt_chunks_contains_metadata():
    receipt = Receipt(
        id=10,
        user_id=3,
        image_path="receipt.png",
        raw_text="BACH HOA XANH\nTong Cong\n531,000 VND",
        supplier_name="BACH HOA XANH",
        receipt_date="13/05/2025",
        total_amount=531000,
        status="Approved",
    )
    receipt.items = [
        ReceiptItem(item_name="Sua chua", quantity=1, unit_price=36000, amount=36000)
    ]

    chunks = build_receipt_chunks(receipt)

    assert {chunk.metadata["chunk_type"] for chunk in chunks} == {"summary", "items", "raw"}
    assert chunks[0].metadata["user_id"] == 3
    assert chunks[0].metadata["receipt_id"] == 10
    assert chunks[0].metadata["receipt_key"] == "3:10"
    assert "BACH HOA XANH" in chunks[0].document


def test_normalize_for_search_removes_vietnamese_accents():
    assert normalize_for_search("Tổng tiền hóa đơn Bách Hóa Xanh") == (
        "tong tien hoa don bach hoa xanh"
    )

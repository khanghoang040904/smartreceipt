from unittest.mock import patch

from app.models.receipt import Receipt, ReceiptItem
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.chat_service import answer_chat


def _create_user(db, email: str) -> User:
    user = User(email=email, full_name=email, password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_receipt(db, user_id: int, supplier: str, total: float, raw_text: str) -> Receipt:
    receipt = Receipt(
        user_id=user_id,
        image_path=f"{supplier.lower().replace(' ', '_')}.png",
        raw_text=raw_text,
        supplier_name=supplier,
        receipt_date="13/05/2025",
        total_amount=total,
        status="Approved",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def _add_item(db, receipt_id: int, name: str, quantity: int, unit_price: float, amount: float) -> ReceiptItem:
    item = ReceiptItem(
        receipt_id=receipt_id,
        item_name=name,
        quantity=quantity,
        unit_price=unit_price,
        amount=amount,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@patch("app.services.chat_service.chat_with_context")
def test_chat_gemini_uses_user_scope(mock_gemini, db_session):
    user = _create_user(db_session, "owner@test.com")
    other_user = _create_user(db_session, "other@test.com")
    _create_receipt(
        db_session, user.id, "BACH HOA XANH", 531000,
        "BACH HOA XANH\nTong Cong\n531,000 VND",
    )
    _create_receipt(
        db_session, other_user.id, "BACH HOA XANH", 999999,
        "Private receipt",
    )

    mock_gemini.return_value = "Tổng tiền hóa đơn Bach Hoa Xanh là 531.000 đ."

    response = answer_chat(
        ChatRequest(message="Tong tien hoa don Bach Hoa Xanh la bao nhieu?"),
        user.id,
        db_session,
    )

    assert response.route == "gemini"
    assert "531" in response.answer
    receipt_ids = {s.receipt_id for s in response.sources}
    assert all(
        db_session.query(Receipt).filter(Receipt.id == rid, Receipt.user_id == user.id).first()
        for rid in receipt_ids
    )


@patch("app.services.chat_service.chat_with_context")
def test_chat_gemini_does_not_leak_other_users(mock_gemini, db_session):
    user = _create_user(db_session, "searcher@test.com")
    other_user = _create_user(db_session, "hidden@test.com")
    receipt = _create_receipt(
        db_session, user.id, "BACH HOA XANH", 531000,
        "TT: ZaloPay\nMa GD: ZLP250513182201",
    )
    _create_receipt(
        db_session, other_user.id, "SECRET SHOP", 1000,
        "ZaloPay private data",
    )

    mock_gemini.return_value = "Tìm thấy hóa đơn ZaloPay từ BACH HOA XANH."

    response = answer_chat(ChatRequest(message="ZaloPay"), user.id, db_session)

    assert response.route == "gemini"
    for source in response.sources:
        assert source.receipt_id == receipt.id


@patch("app.services.chat_service.chat_with_context")
def test_chat_empty_message_returns_prompt(mock_gemini, db_session):
    user = _create_user(db_session, "empty@test.com")

    response = answer_chat(ChatRequest(message=""), user.id, db_session)

    assert response.route == "empty"
    mock_gemini.assert_not_called()


@patch("app.services.chat_service.chat_with_context")
def test_chat_no_receipts_returns_empty(mock_gemini, db_session):
    user = _create_user(db_session, "nodata@test.com")

    mock_gemini.return_value = None

    response = answer_chat(
        ChatRequest(message="Tong chi tieu thang nay?"),
        user.id,
        db_session,
    )

    assert response.route == "gemini"
    assert response.confidence == 0.0


@patch("app.services.chat_service.chat_with_context")
def test_chat_gemini_returns_answer_with_sources(mock_gemini, db_session):
    user = _create_user(db_session, "withdata@test.com")
    receipt = _create_receipt(
        db_session, user.id, "BACH HOA XANH", 531000,
        "BACH HOA XANH\nTong Cong 531,000 VND",
    )
    _add_item(db_session, receipt.id, "Ca chua (kg)", 1, 32000, 32000)

    mock_gemini.return_value = "Bạn đã mua Cà chua (kg) với giá 32.000 đ tại BACH HOA XANH."

    response = answer_chat(
        ChatRequest(message="Gia Ca chua la bao nhieu?"),
        user.id,
        db_session,
    )

    assert response.route == "gemini"
    assert response.confidence == 0.9
    assert len(response.sources) > 0
    assert "32.000" in response.answer

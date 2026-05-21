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


def test_chat_sql_receipt_total_uses_user_scope(db_session):
    user = _create_user(db_session, "owner@test.com")
    other_user = _create_user(db_session, "other@test.com")
    receipt = _create_receipt(
        db_session,
        user.id,
        "BACH HOA XANH",
        531000,
        "BACH HOA XANH\nTong Cong\n531,000 VND\nTT: ZaloPay",
    )
    _create_receipt(
        db_session,
        other_user.id,
        "BACH HOA XANH",
        999999,
        "Private receipt",
    )

    response = answer_chat(
        ChatRequest(message="Tong tien hoa don Bach Hoa Xanh la bao nhieu?"),
        user.id,
        db_session,
    )

    assert response.route == "sql"
    assert response.sql_result["receipt_id"] == receipt.id
    assert response.sql_result["total_amount"] == 531000
    assert response.sources[0].receipt_id == receipt.id


def test_chat_hybrid_search_does_not_leak_other_users(db_session):
    user = _create_user(db_session, "searcher@test.com")
    other_user = _create_user(db_session, "hidden@test.com")
    receipt = _create_receipt(
        db_session,
        user.id,
        "BACH HOA XANH",
        531000,
        "TT: ZaloPay\nMa GD: ZLP250513182201",
    )
    _create_receipt(
        db_session,
        other_user.id,
        "SECRET SHOP",
        1000,
        "ZaloPay private data",
    )

    response = answer_chat(ChatRequest(message="ZaloPay"), user.id, db_session)

    assert response.route == "hybrid"
    assert response.sources
    assert {source.receipt_id for source in response.sources} == {receipt.id}


def test_chat_item_price_uses_saved_receipt_items(db_session):
    user = _create_user(db_session, "items@test.com")
    receipt = _create_receipt(
        db_session,
        user.id,
        "BACH HOA XANH",
        531000,
        "BACH HOA XANH\nCa chua (kg)\n32,000\nTong Cong\n531,000 VND",
    )
    electronics = _create_receipt(
        db_session,
        user.id,
        "DIEN MAY XANH",
        8760000,
        "DIEN MAY XANH\nTong tien hang\n8,760,000",
    )
    _add_item(db_session, receipt.id, "Ca chua (kg)", 1, 32000, 32000)
    _add_item(db_session, electronics.id, "May loc khong khi", 1, 4500000, 4500000)

    response = answer_chat(
        ChatRequest(message="Gia Ca chua (kg) la bao nhieu?"),
        user.id,
        db_session,
    )

    assert response.route == "item"
    assert response.sql_result["items"][0]["receipt_id"] == receipt.id
    assert response.sql_result["items"][0]["unit_price"] == 32000
    assert response.sources[0].receipt_id == receipt.id
    assert electronics.supplier_name not in response.answer


def test_chat_item_lookup_returns_no_data_instead_of_guessing(db_session):
    user = _create_user(db_session, "empty-items@test.com")
    receipt = _create_receipt(
        db_session,
        user.id,
        "BACH HOA XANH",
        531000,
        "BACH HOA XANH\nTong Cong\n531,000 VND",
    )
    _add_item(db_session, receipt.id, "Ca chua (kg)", 1, 32000, 32000)

    response = answer_chat(
        ChatRequest(message="Gia ca phe sua da la bao nhieu?"),
        user.id,
        db_session,
    )

    assert response.route == "item"
    assert response.sources == []
    assert response.confidence == 0.0


def test_chat_item_search_returns_only_receipts_with_matching_item(db_session):
    user = _create_user(db_session, "item-search@test.com")
    rau_receipt = _create_receipt(
        db_session,
        user.id,
        "SIEU THI CO. OPMART",
        575225,
        "SIEU THI CO. OPMART\nRau muong (bo)\n16,000",
    )
    other_receipt = _create_receipt(
        db_session,
        user.id,
        "DIEN MAY XANH",
        8760000,
        "DIEN MAY XANH\nMay loc khong khi\n4,500,000",
    )
    _add_item(db_session, rau_receipt.id, "Rau muong (bo)", 1, 16000, 16000)
    _add_item(db_session, other_receipt.id, "May loc khong khi", 1, 4500000, 4500000)

    response = answer_chat(
        ChatRequest(message="Tim hoa don co rau muong"),
        user.id,
        db_session,
    )

    assert response.route == "item"
    assert {source.receipt_id for source in response.sources} == {rau_receipt.id}
    assert response.sql_result["items"][0]["receipt_id"] == rau_receipt.id


def test_chat_item_search_no_match_does_not_return_receipt_history(db_session):
    user = _create_user(db_session, "item-no-match@test.com")
    receipt = _create_receipt(
        db_session,
        user.id,
        "BACH HOA XANH",
        531000,
        "BACH HOA XANH\nCa chua\n32,000",
    )
    _add_item(db_session, receipt.id, "Ca chua", 1, 32000, 32000)

    response = answer_chat(
        ChatRequest(message="Tim hoa don co kep toc"),
        user.id,
        db_session,
    )

    assert response.route == "item"
    assert response.sources == []
    assert response.confidence == 0.0

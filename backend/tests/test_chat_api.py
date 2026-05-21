from app.models.receipt import Receipt, ReceiptItem
from app.models.user import User


def test_chat_api_returns_receipt_total(client, auth_headers, db_session):
    user = db_session.query(User).filter(User.email == "testuser@test.com").first()
    receipt = Receipt(
        user_id=user.id,
        image_path="bach_hoa_xanh.png",
        raw_text="BACH HOA XANH\nTong Cong\n531,000 VND",
        supplier_name="BACH HOA XANH",
        receipt_date="13/05/2025",
        total_amount=531000,
        status="Approved",
    )
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)

    response = client.post(
        "/api/chat",
        json={"message": "Tong tien hoa don Bach Hoa Xanh la bao nhieu?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "sql"
    assert data["sql_result"]["receipt_id"] == receipt.id
    assert data["sql_result"]["total_amount"] == 531000
    assert data["sources"][0]["receipt_id"] == receipt.id


def test_chat_api_returns_item_price(client, auth_headers, db_session):
    user = db_session.query(User).filter(User.email == "testuser@test.com").first()
    receipt = Receipt(
        user_id=user.id,
        image_path="bach_hoa_xanh.png",
        raw_text="BACH HOA XANH\nCa chua (kg)\n32,000 VND",
        supplier_name="BACH HOA XANH",
        receipt_date="13/05/2025",
        total_amount=531000,
        status="Approved",
    )
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    db_session.add(ReceiptItem(
        receipt_id=receipt.id,
        item_name="Ca chua (kg)",
        quantity=1,
        unit_price=32000,
        amount=32000,
    ))
    db_session.commit()

    response = client.post(
        "/api/chat",
        json={"message": "Giá Ca chua (kg) là bao nhiêu?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "item"
    assert data["sql_result"]["items"][0]["receipt_id"] == receipt.id
    assert data["sql_result"]["items"][0]["unit_price"] == 32000

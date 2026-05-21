from app.models.budget import Budget
from app.models.category import Category
from app.models.receipt import Receipt
from app.models.user import User


def _current_user(db_session):
    return db_session.query(User).filter(User.email == "testuser@test.com").first()


def _category(db_session, user_id: int, name: str = "Thực phẩm") -> Category:
    category = db_session.query(Category).filter(Category.user_id == user_id, Category.name == name).first()
    assert category is not None
    return category


def test_get_budgets_includes_spending_by_month(client, auth_headers, db_session):
    user = _current_user(db_session)
    category = _category(db_session, user.id)
    db_session.add(Receipt(
        user_id=user.id,
        image_path="food.png",
        raw_text="Rau muống",
        supplier_name="SIEU THI",
        receipt_date="10/05/2025",
        total_amount=120000,
        category_id=category.id,
        status="Đã duyệt",
    ))
    db_session.commit()

    response = client.put(
        "/api/budgets",
        json={"category_id": category.id, "month": "2025-05", "amount": 200000},
        headers=auth_headers,
    )
    assert response.status_code == 200

    response = client.get("/api/budgets?month=2025-05", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    food = next(item for item in data["categories"] if item["category_id"] == category.id)
    assert food["budget_amount"] == 200000
    assert food["spent_amount"] == 120000
    assert food["remaining_amount"] == 80000
    assert food["usage_percent"] == 60
    assert food["status"] == "ok"


def test_budget_warning_and_over_status(client, auth_headers, db_session):
    user = _current_user(db_session)
    category = _category(db_session, user.id)
    db_session.add(Receipt(
        user_id=user.id,
        image_path="food.png",
        raw_text="Rau muống",
        supplier_name="SIEU THI",
        receipt_date="10/05/2025",
        total_amount=90000,
        category_id=category.id,
        status="Đã duyệt",
    ))
    db_session.commit()

    response = client.put(
        "/api/budgets",
        json={"category_id": category.id, "month": "2025-05", "amount": 100000},
        headers=auth_headers,
    )
    assert response.json()["status"] == "warning"

    response = client.put(
        "/api/budgets",
        json={"category_id": category.id, "month": "2025-05", "amount": 80000},
        headers=auth_headers,
    )
    assert response.json()["status"] == "over"


def test_delete_budget(client, auth_headers, db_session):
    user = _current_user(db_session)
    category = _category(db_session, user.id)
    budget = Budget(user_id=user.id, category_id=category.id, month="2025-05", amount=100000)
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)

    response = client.delete(f"/api/budgets/{budget.id}", headers=auth_headers)
    assert response.status_code == 200

    response = client.get("/api/budgets?month=2025-05", headers=auth_headers)
    category_summary = next(item for item in response.json()["categories"] if item["category_id"] == category.id)
    assert category_summary["budget_id"] is None
    assert category_summary["budget_amount"] == 0


def test_budget_does_not_leak_other_users(client, auth_headers, db_session):
    user = _current_user(db_session)
    other = User(email="other-budget@test.com", full_name="Other", password_hash="hash")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    other_category = Category(name="Thực phẩm", user_id=other.id)
    db_session.add(other_category)
    db_session.commit()
    db_session.refresh(other_category)
    db_session.add(Budget(user_id=other.id, category_id=other_category.id, month="2025-05", amount=999999))
    db_session.commit()

    response = client.get("/api/budgets?month=2025-05", headers=auth_headers)
    assert response.status_code == 200
    assert all(item["budget_amount"] != 999999 for item in response.json()["categories"])

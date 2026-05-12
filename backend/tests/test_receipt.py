# TC7: Get receipts (empty)
def test_list_receipts_empty(client, auth_headers):
    response = client.get("/api/receipts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


# TC8: Get categories (auto-created on registration)
def test_categories_created_on_register(client, auth_headers):
    response = client.get("/api/categories", headers=auth_headers)
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 4
    names = [c["name"] for c in categories]
    assert "Thực phẩm" in names
    assert "Đồ uống" in names


# TC9: Create a new category
def test_create_category(client, auth_headers):
    response = client.post("/api/categories", json={"name": "Vận chuyển"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Vận chuyển"


# TC10: Get dashboard stats
def test_dashboard_stats(client, auth_headers):
    response = client.get("/api/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_receipts"] == 0
    assert data["stats"]["total_spending"] == 0.0
    assert "monthly_spending" in data


# TC11: Delete a category
def test_delete_category(client, auth_headers):
    cat = client.post("/api/categories", json={"name": "Temp"}, headers=auth_headers)
    cat_id = cat.json()["id"]
    response = client.delete(f"/api/categories/{cat_id}", headers=auth_headers)
    assert response.status_code == 200

    cats = client.get("/api/categories", headers=auth_headers)
    names = [c["name"] for c in cats.json()]
    assert "Temp" not in names


# TC12: Export CSV
def test_export_csv(client, auth_headers):
    response = client.get("/api/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

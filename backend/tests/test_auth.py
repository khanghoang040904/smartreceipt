# TC1: Register successfully
def test_register_success(client):
    response = client.post("/api/auth/register", json={
        "email": "user@test.com",
        "full_name": "Nguyen Van A",
        "password": "Test1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user@test.com"
    assert data["user"]["full_name"] == "Nguyen Van A"


# TC2: Register with duplicate email
def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "email": "dup@test.com",
        "full_name": "User 1",
        "password": "Test1234",
    })
    response = client.post("/api/auth/register", json={
        "email": "dup@test.com",
        "full_name": "User 2",
        "password": "Test1234",
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


# TC3: Login successfully
def test_login_success(client):
    client.post("/api/auth/register", json={
        "email": "login@test.com",
        "full_name": "Login User",
        "password": "Test1234",
    })
    response = client.post("/api/auth/login", json={
        "email": "login@test.com",
        "password": "Test1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@test.com"


# TC4: Login with wrong password
def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "wrong@test.com",
        "full_name": "Wrong User",
        "password": "Test1234",
    })
    response = client.post("/api/auth/login", json={
        "email": "wrong@test.com",
        "password": "WrongPass",
    })
    assert response.status_code == 401


# TC5: Get current user (authenticated)
def test_get_me(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@test.com"


# TC6: Access protected route without token
def test_unauthorized_access(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 403

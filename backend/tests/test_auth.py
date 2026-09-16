def test_register_user(client, create_user):

    data = create_user()
    
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"
    assert "id" in data


def test_register_duplicate_email(client, create_user):
    create_user()
    
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "anotheruser",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 409


def test_register_duplicate_username(client, create_user):
    create_user()
    
    response = client.post(
        "/auth/register",
        json={
            "email": "another@example.com",
            "username": "user",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 409


def test_login_wrong_password(client, create_user):
    create_user()
    
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401


def test_login_success(client, create_user):
    create_user()
    
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client, create_user, login_user, auth_headers):
    create_user()
    
    token = login_user()
    
    response = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_refresh_token(client, create_user):
    create_user()
    
    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


def test_logout(client, create_user):
    create_user()
    
    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )
    assert response.status_code == 204
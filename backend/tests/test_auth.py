def create_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    return response


def login_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200

    return response


def test_register_user(client):
    response = create_user(client)

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


def test_register_duplicate_email(client):
    create_user(client)

    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "anotheruser",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 409


def test_register_duplicate_username(client):
    create_user(client)

    response = client.post(
        "/auth/register",
        json={
            "email": "another@example.com",
            "username": "testuser",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 409


def test_login_wrong_password(client):
    create_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_success(client):
    create_user(client)

    response = login_user(client)

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client):
    create_user(client)

    login_response = login_user(client)
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_token(client):
    create_user(client)

    login_response = login_user(client)
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


def test_logout(client):
    create_user(client)

    login_response = login_user(client)
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 204
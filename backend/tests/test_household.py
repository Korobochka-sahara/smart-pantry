def create_user(
    client,
    email="user@example.com",
    username="user",
    password="StrongPassword123!",
):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(
    client,
    email="user@example.com",
    password="StrongPassword123!",
):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_household(client, token, name="My Household"):
    response = client.post(
        "/households",
        headers=auth_headers(token),
        json={
            "name": name,
        },
    )

    assert response.status_code == 201

    return response.json()


# ---------------------------------------------------------
# Создание
# ---------------------------------------------------------


def test_create_household(client):
    create_user(client)

    token = login_user(client)

    response = client.post(
        "/households",
        headers=auth_headers(token),
        json={
            "name": "My Household",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["name"] == "My Household"


def test_create_household_without_token(client):
    response = client.post(
        "/households",
        json={
            "name": "My Household",
        },
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Получение household
# ---------------------------------------------------------


def test_get_my_households(client):
    create_user(client)

    token = login_user(client)

    create_household(client, token, "Household 1")
    create_household(client, token, "Household 2")

    response = client.get(
        "/households",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Household 1"
    assert data[1]["name"] == "Household 2"


def test_get_household(client):
    create_user(client)

    token = login_user(client)

    household = create_household(
        client,
        token,
        "My Household",
    )

    response = client.get(
        f"/households/{household['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == household["id"]
    assert data["name"] == "My Household"


def test_get_nonexistent_household(client):
    create_user(client)

    token = login_user(client)

    response = client.get(
        "/households/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_user_cannot_access_foreign_household(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    outsider = create_user(
        client,
        email="outsider@example.com",
        username="outsider",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    outsider_token = login_user(
        client,
        outsider["email"],
    )

    household = create_household(
        client,
        owner_token,
        "Private Household",
    )

    response = client.get(
        f"/households/{household['id']}",
        headers=auth_headers(outsider_token),
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Участники
# ---------------------------------------------------------


def test_creator_is_owner(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        token,
        "My Household",
    )

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    members = response.json()

    assert len(members) == 1
    assert members[0]["user_id"] == owner["id"]
    assert members[0]["role"] == "OWNER"


def test_get_household_members(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 200

    members = response.json()

    assert len(members) == 2

    user_ids = {item["user_id"] for item in members}

    assert owner["id"] in user_ids
    assert member["id"] in user_ids


def test_owner_can_add_member(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == member["id"]
    assert data["role"] == "MEMBER"


def test_member_cannot_add_member(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    another_member = create_user(
        client,
        email="another@example.com",
        username="another",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    member_token = login_user(
        client,
        member["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(member_token),
        json={
            "user_id": another_member["id"],
        },
    )

    assert response.status_code == 403


def test_outsider_cannot_get_members(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    outsider = create_user(
        client,
        email="outsider@example.com",
        username="outsider",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    outsider_token = login_user(
        client,
        outsider["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(outsider_token),
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Роли
# ---------------------------------------------------------


def test_owner_can_change_member_role(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/members/{member['id']}/role",
        headers=auth_headers(owner_token),
        json={
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == member["id"]
    assert data["role"] == "ADMIN"


def test_member_cannot_change_roles(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    another_member = create_user(
        client,
        email="another@example.com",
        username="another",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    member_token = login_user(
        client,
        member["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": another_member["id"],
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/members/{another_member['id']}/role",
        headers=auth_headers(member_token),
        json={
            "role": "ADMIN",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_change_owner_role(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    admin = create_user(
        client,
        email="admin@example.com",
        username="admin",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": admin["id"],
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/members/{admin['id']}/role",
        headers=auth_headers(owner_token),
        json={
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200

    admin_token = login_user(
        client,
        admin["email"],
    )

    response = client.patch(
        f"/households/{household['id']}/members/{owner['id']}/role",
        headers=auth_headers(admin_token),
        json={
            "role": "MEMBER",
        },
    )

    assert response.status_code == 403


# ---------------------------------------------------------
# Удаление участников
# ---------------------------------------------------------


def test_owner_can_remove_member(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    assert response.status_code == 201

    response = client.delete(
        f"/households/{household['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 200

    members = response.json()

    assert len(members) == 1
    assert members[0]["user_id"] == owner["id"]


def test_member_cannot_remove_member(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    another_member = create_user(
        client,
        email="another@example.com",
        username="another",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": another_member["id"],
        },
    )

    member_token = login_user(
        client,
        member["email"],
    )

    response = client.delete(
        f"/households/{household['id']}/members/{another_member['id']}",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 403


# ---------------------------------------------------------
# Выход из household
# ---------------------------------------------------------


def test_member_can_leave_household(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    member = create_user(
        client,
        email="member@example.com",
        username="member",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
        },
    )

    member_token = login_user(
        client,
        member["email"],
    )

    response = client.post(
        f"/households/{household['id']}/leave",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 204

    response = client.get(
        "/households",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_owner_leaves_and_admin_becomes_owner(client):
    owner = create_user(
        client,
        email="owner@example.com",
        username="owner",
    )

    admin = create_user(
        client,
        email="admin@example.com",
        username="admin",
    )

    owner_token = login_user(
        client,
        owner["email"],
    )

    household = create_household(
        client,
        owner_token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": admin["id"],
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/members/{admin['id']}/role",
        headers=auth_headers(owner_token),
        json={
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200

    admin_token = login_user(
        client,
        admin["email"],
    )

    response = client.post(
        f"/households/{household['id']}/leave",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    members = response.json()

    assert len(members) == 1
    assert members[0]["user_id"] == admin["id"]
    assert members[0]["role"] == "OWNER"


def test_owner_alone_leaves_household(client):
    create_user(client)

    token = login_user(client)

    household = create_household(
        client,
        token,
    )

    response = client.post(
        f"/households/{household['id']}/leave",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/households/{household['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Лимит household
# ---------------------------------------------------------


def test_user_can_create_max_five_households(client):
    create_user(client)

    token = login_user(client)

    for number in range(1, 6):
        response = client.post(
            "/households",
            headers=auth_headers(token),
            json={
                "name": f"Household {number}",
            },
        )

        assert response.status_code == 201

    response = client.post(
        "/households",
        headers=auth_headers(token),
        json={
            "name": "Household 6",
        },
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# Несуществующие участники / household
# ---------------------------------------------------------


def test_add_nonexistent_user(client):
    create_user(client)

    token = login_user(client)

    household = create_household(
        client,
        token,
    )

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(token),
        json={
            "user_id": 999999,
        },
    )

    assert response.status_code in (404, 409)


def test_add_member_to_nonexistent_household(client):
    create_user(client)

    token = login_user(client)

    response = client.post(
        "/households/999999/members",
        headers=auth_headers(token),
        json={
            "user_id": 1,
        },
    )

    assert response.status_code == 404
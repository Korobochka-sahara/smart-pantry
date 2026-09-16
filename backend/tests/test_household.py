# ---------------------------------------------------------
# Создание
# ---------------------------------------------------------

def test_create_household(client, create_user, login_user, auth_headers):
    create_user()
    token = login_user()

    response = client.post(
        "/households",
        headers=auth_headers(token),
        json={"name": "My Household"},
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "My Household"


def test_create_household_without_token(client):
    response = client.post(
        "/households",
        json={"name": "My Household"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------
# Получение household
# ---------------------------------------------------------

def test_get_my_households(client, create_user, login_user, auth_headers, create_household):
    create_user()
    token = login_user()

    create_household(token, "Household 1")
    create_household(token, "Household 2")

    response = client.get("/households", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Household 1"
    assert data[1]["name"] == "Household 2"


def test_get_household(client, create_user, login_user, auth_headers, create_household):
    create_user()
    token = login_user()

    household = create_household(token, "My Household")

    response = client.get(
        f"/households/{household['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == household["id"]
    assert data["name"] == "My Household"


def test_get_nonexistent_household(client, create_user, login_user, auth_headers):
    create_user()
    token = login_user()

    response = client.get("/households/999999", headers=auth_headers(token))
    assert response.status_code == 404


def test_user_cannot_access_foreign_household(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    outsider = create_user(email="outsider@example.com", username="outsider")

    owner_token = login_user(email=owner["email"])
    outsider_token = login_user(email=outsider["email"])

    household = create_household(owner_token, "Private Household")

    response = client.get(
        f"/households/{household['id']}",
        headers=auth_headers(outsider_token),
    )
    assert response.status_code == 404


# ---------------------------------------------------------
# Участники
# ---------------------------------------------------------

def test_creator_is_owner(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    token = login_user(email=owner["email"])

    household = create_household(token, "My Household")

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    members = response.json()

    assert len(members) == 1
    assert members[0]["user_id"] == owner["id"]
    assert members[0]["role"] == "OWNER"


def test_get_household_members(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")

    owner_token = login_user(email=owner["email"])
    household = create_household(owner_token)

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
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


def test_owner_can_add_member(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")

    owner_token = login_user(email=owner["email"])
    household = create_household(owner_token)

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == member["id"]
    assert data["role"] == "MEMBER"


def test_member_cannot_add_member(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")
    another_member = create_user(email="another@example.com", username="another")

    owner_token = login_user(email=owner["email"])
    member_token = login_user(email=member["email"])

    household = create_household(owner_token)

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )
    assert response.status_code == 201

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(member_token),
        json={"user_id": another_member["id"]},
    )
    assert response.status_code == 403


def test_outsider_cannot_get_members(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    outsider = create_user(email="outsider@example.com", username="outsider")

    owner_token = login_user(email=owner["email"])
    outsider_token = login_user(email=outsider["email"])

    household = create_household(owner_token)

    response = client.get(
        f"/households/{household['id']}/members",
        headers=auth_headers(outsider_token),
    )
    assert response.status_code == 404


# ---------------------------------------------------------
# Роли
# ---------------------------------------------------------

def test_owner_can_change_member_role(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")

    owner_token = login_user(email=owner["email"])
    household = create_household(owner_token)

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )
    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/members/{member['id']}/role",
        headers=auth_headers(owner_token),
        json={"role": "ADMIN"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == member["id"]
    assert data["role"] == "ADMIN"


def test_member_cannot_change_roles(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")
    another_member = create_user(email="another@example.com", username="another")

    owner_token = login_user(email=owner["email"])
    member_token = login_user(email=member["email"])

    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )
    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": another_member["id"]},
    )

    response = client.patch(
        f"/households/{household['id']}/members/{another_member['id']}/role",
        headers=auth_headers(member_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 403


def test_admin_cannot_change_owner_role(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    admin = create_user(email="admin@example.com", username="admin")

    owner_token = login_user(email=owner["email"])
    admin_token = login_user(email=admin["email"])

    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": admin["id"]},
    )
    client.patch(
        f"/households/{household['id']}/members/{admin['id']}/role",
        headers=auth_headers(owner_token),
        json={"role": "ADMIN"},
    )

    response = client.patch(
        f"/households/{household['id']}/members/{owner['id']}/role",
        headers=auth_headers(admin_token),
        json={"role": "MEMBER"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------
# Удаление участников
# ---------------------------------------------------------

def test_owner_can_remove_member(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")

    owner_token = login_user(email=owner["email"])
    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )

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


def test_member_cannot_remove_member(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")
    another_member = create_user(email="another@example.com", username="another")

    owner_token = login_user(email=owner["email"])
    member_token = login_user(email=member["email"])

    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )
    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": another_member["id"]},
    )

    response = client.delete(
        f"/households/{household['id']}/members/{another_member['id']}",
        headers=auth_headers(member_token),
    )
    assert response.status_code == 403


# ---------------------------------------------------------
# Выход из household
# ---------------------------------------------------------

def test_member_can_leave_household(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    member = create_user(email="member@example.com", username="member")

    owner_token = login_user(email=owner["email"])
    member_token = login_user(email=member["email"])

    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": member["id"]},
    )

    response = client.post(
        f"/households/{household['id']}/leave",
        headers=auth_headers(member_token),
    )
    assert response.status_code == 204

    response = client.get("/households", headers=auth_headers(member_token))
    assert response.status_code == 200
    assert response.json() == []


def test_owner_leaves_and_admin_becomes_owner(client, create_user, login_user, auth_headers, create_household):
    owner = create_user(email="owner@example.com", username="owner")
    admin = create_user(email="admin@example.com", username="admin")

    owner_token = login_user(email=owner["email"])
    admin_token = login_user(email=admin["email"])

    household = create_household(owner_token)

    client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(owner_token),
        json={"user_id": admin["id"]},
    )
    client.patch(
        f"/households/{household['id']}/members/{admin['id']}/role",
        headers=auth_headers(owner_token),
        json={"role": "ADMIN"},
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


def test_owner_alone_leaves_household(client, create_user, login_user, auth_headers, create_household):
    create_user()
    token = login_user()

    household = create_household(token)

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

def test_user_can_create_max_five_households(client, create_user, login_user, auth_headers, create_household):
    create_user()
    token = login_user()

    for number in range(1, 6):
        response = client.post(
            "/households",
            headers=auth_headers(token),
            json={"name": f"Household {number}"},
        )
        assert response.status_code == 201

    response = client.post(
        "/households",
        headers=auth_headers(token),
        json={"name": "Household 6"},
    )
    assert response.status_code == 409


# ---------------------------------------------------------
# Несуществующие участники / household
# ---------------------------------------------------------

def test_add_nonexistent_user(client, create_user, login_user, auth_headers, create_household):
    create_user()
    token = login_user()

    household = create_household(token)

    response = client.post(
        f"/households/{household['id']}/members",
        headers=auth_headers(token),
        json={"user_id": 999999},
    )
    assert response.status_code in (404, 409)


def test_add_member_to_nonexistent_household(client, create_user, login_user, auth_headers):
    create_user()
    token = login_user()

    response = client.post(
        "/households/999999/members",
        headers=auth_headers(token),
        json={"user_id": 1},
    )
    assert response.status_code == 404
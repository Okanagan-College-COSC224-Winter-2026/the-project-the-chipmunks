"""
Tests for admin user management endpoints (US26).
"""

import json


def _login_as_admin(test_client, make_admin):
    """Helper: create an admin and log in, returning the admin user."""
    admin = make_admin(email="admin@test.com", password="adminpass", name="Admin")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@test.com", "password": "adminpass"}),
        headers={"Content-Type": "application/json"},
    )
    return admin


def _create_student(test_client):
    """Helper: register a student via the public endpoint."""
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "Student User", "email": "student@test.com", "password": "123456"}),
        headers={"Content-Type": "application/json"},
    )


# ---- GET /admin/users ----

def test_list_users_as_admin(test_client, make_admin):
    """Admin can list users with paginated response."""
    _login_as_admin(test_client, make_admin)
    r = test_client.get("/admin/users")
    assert r.status_code == 200
    data = r.json
    assert "users" in data
    assert "total" in data
    assert "pages" in data
    assert "page" in data


def test_list_users_forbidden_for_student(test_client):
    """Non-admin users get 403."""
    # Register and login as student
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "Stu", "email": "stu@test.com", "password": "123456"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "stu@test.com", "password": "123456"}),
        headers={"Content-Type": "application/json"},
    )
    r = test_client.get("/admin/users")
    assert r.status_code == 403


def test_list_users_with_role_filter(test_client, make_admin):
    """Admin can filter users by role."""
    _login_as_admin(test_client, make_admin)
    _create_student(test_client)

    r = test_client.get("/admin/users?role=student")
    assert r.status_code == 200
    for u in r.json["users"]:
        assert u["role"] == "student"


def test_list_users_with_search(test_client, make_admin):
    """Admin can search users by name or email."""
    _login_as_admin(test_client, make_admin)
    _create_student(test_client)

    r = test_client.get("/admin/users?search=student")
    assert r.status_code == 200
    assert r.json["total"] >= 1


# ---- POST /admin/users/create ----

def test_create_user(test_client, make_admin):
    """Admin can create a new user."""
    _login_as_admin(test_client, make_admin)

    payload = {
        "name": "New User",
        "email": "new@test.com",
        "password": "Pass1234!",
        "role": "student",
    }
    r = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 201
    assert r.json["user"]["email"] == "new@test.com"


def test_create_user_duplicate_email(test_client, make_admin):
    """Creating a user with an existing email returns 409."""
    _login_as_admin(test_client, make_admin)

    payload = {
        "name": "First",
        "email": "dup@test.com",
        "password": "Pass1234!",
        "role": "teacher",
    }
    test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    r = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 409


# ---- PUT /admin/users/<id> ----

def test_update_user(test_client, make_admin):
    """Admin can update a user's name and email."""
    _login_as_admin(test_client, make_admin)

    # Create a user to update
    payload = {
        "name": "Original",
        "email": "original@test.com",
        "password": "Pass1234!",
        "role": "student",
    }
    create_resp = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    user_id = create_resp.json["user"]["id"]

    update_payload = {"name": "Updated Name", "role": "teacher"}
    r = test_client.put(
        f"/admin/users/{user_id}",
        data=json.dumps(update_payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json["user"]["name"] == "Updated Name"
    assert r.json["user"]["role"] == "teacher"


# ---- PATCH /admin/users/<id>/deactivate & /reactivate ----

def test_deactivate_user(test_client, make_admin):
    """Admin can deactivate a user."""
    _login_as_admin(test_client, make_admin)

    # Create a user to deactivate
    payload = {
        "name": "Deactivate Me",
        "email": "deactivate@test.com",
        "password": "Pass1234!",
        "role": "student",
    }
    create_resp = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    user_id = create_resp.json["user"]["id"]

    r = test_client.patch(f"/admin/users/{user_id}/deactivate")
    assert r.status_code == 200
    assert r.json["msg"] == "User deactivated"


def test_cannot_deactivate_self(test_client, make_admin):
    """Admin cannot deactivate their own account."""
    admin = _login_as_admin(test_client, make_admin)

    r = test_client.patch(f"/admin/users/{admin.id}/deactivate")
    assert r.status_code == 400


def test_reactivate_user(test_client, make_admin):
    """Admin can reactivate a deactivated user."""
    _login_as_admin(test_client, make_admin)

    # Create and deactivate
    payload = {
        "name": "Reactivate Me",
        "email": "reactivate@test.com",
        "password": "Pass1234!",
        "role": "student",
    }
    create_resp = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    user_id = create_resp.json["user"]["id"]
    test_client.patch(f"/admin/users/{user_id}/deactivate")

    r = test_client.patch(f"/admin/users/{user_id}/reactivate")
    assert r.status_code == 200
    assert r.json["msg"] == "User reactivated"


# ---- Deactivated user blocked at login ----

def test_deactivated_user_cannot_login(test_client, make_admin):
    """A deactivated user gets 403 when trying to log in."""
    _login_as_admin(test_client, make_admin)

    # Create a user
    payload = {
        "name": "Will Be Blocked",
        "email": "blocked@test.com",
        "password": "Pass1234!",
        "role": "student",
    }
    create_resp = test_client.post(
        "/admin/users/create",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    user_id = create_resp.json["user"]["id"]

    # Deactivate
    test_client.patch(f"/admin/users/{user_id}/deactivate")

    # Logout admin
    test_client.post("/auth/logout")

    # Try to login as the deactivated user
    r = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "blocked@test.com", "password": "Pass1234!"}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 403
    assert "deactivated" in r.json["msg"].lower()

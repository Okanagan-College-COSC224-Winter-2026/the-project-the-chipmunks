import json
from werkzeug.security import generate_password_hash
from api.models import User
from api.models.db import db as _db


def _create_user(name, email, password="password123", role="student"):
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash(password),
        role=role,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(test_client, email, password="password123"):
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def test_get_profile_returns_user_fields(test_client, db):
    _create_user("Test Student", "student@test.com")
    _login(test_client, "student@test.com")
    r = test_client.get("/user/profile")
    assert r.status_code == 200
    for field in ["id", "name", "email", "role"]:
        assert field in r.json


def test_update_profile_name(test_client, db):
    _create_user("Test Student", "student@test.com")
    _login(test_client, "student@test.com")
    r = test_client.put(
        "/user/profile",
        data=json.dumps({"name": "UpdatedName"}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json["name"] == "UpdatedName"


def test_email_change_is_silently_ignored(test_client, db):
    _create_user("Test Student", "student@test.com")
    _login(test_client, "student@test.com")
    r = test_client.put(
        "/user/profile",
        data=json.dumps({"email": "hacker@evil.com"}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json["email"] == "student@test.com"


def test_empty_name_rejected(test_client, db):
    _create_user("Test Student", "student@test.com")
    _login(test_client, "student@test.com")
    r = test_client.put(
        "/user/profile",
        data=json.dumps({"name": ""}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_unauthenticated_profile_access_rejected(test_client, db):
    r = test_client.get("/user/profile")
    assert r.status_code in (401, 403)

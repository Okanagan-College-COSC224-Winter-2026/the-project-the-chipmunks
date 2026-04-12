"""
Tests for Feature C — Password Management System
Tests for PUT /user/password endpoint and password validation.

Test cases (sprint plan):
    1.  Change password with valid input succeeds
    2.  Wrong current password returns 400
    3.  New password too short rejected
    4.  Missing uppercase rejected
    5.  Missing lowercase rejected
    6.  Missing number rejected
    7.  Special characters accepted
    8.  Can login with new password after change
    9.  Cannot login with old password after change
    10. Unauthenticated request rejected
    + Additional edge-case tests
"""

import json

from werkzeug.security import generate_password_hash

from api.models import User
from api.models.db import db as _db
from api.services.password_validator import validate_password


# ── Helpers ──────────────────────────────────────────────────────────────────


DEFAULT_PASSWORD = "password123"


def _create_user(name, email, password=DEFAULT_PASSWORD, role="student"):
    """Create a user directly in the DB."""
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash(password),
        role=role,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(test_client, email, password=DEFAULT_PASSWORD):
    """Log in a user via the auth endpoint (sets JWT cookie)."""
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _change_password(test_client, current_password, new_password):
    """Call PUT /user/password and return the response."""
    return test_client.put(
        "/user/password",
        data=json.dumps({
            "current_password": current_password,
            "new_password": new_password,
        }),
        headers={"Content-Type": "application/json"},
    )


# ── Unit tests for validate_password() helper ────────────────────────────────


def test_validate_password_valid():
    """A password meeting all criteria returns no failures."""
    assert validate_password("MySecure#1") == []


def test_validate_password_too_short():
    """A password under 8 characters fails the length check."""
    failures = validate_password("Ab1")
    assert "Must be at least 8 characters" in failures


def test_validate_password_no_uppercase():
    """A password with no uppercase letter is rejected."""
    failures = validate_password("mysecure1")
    assert "Must contain at least one uppercase letter" in failures


def test_validate_password_no_lowercase():
    """A password with no lowercase letter is rejected."""
    failures = validate_password("MYSECURE1")
    assert "Must contain at least one lowercase letter" in failures


def test_validate_password_no_number():
    """A password with no digit is rejected."""
    failures = validate_password("MySecurePwd")
    assert "Must contain at least one number" in failures


def test_validate_password_multiple_failures():
    """A weak password returns all applicable failure messages."""
    failures = validate_password("abc")
    assert len(failures) >= 3  # too short, no uppercase, no number


# ── Test 1: Change password with valid input succeeds ─────────────────────────


def test_change_password_success(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they PUT /user/password with correct current and valid new password
    THEN the server responds 200 with success message
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "NewSecure#1")

    assert resp.status_code == 200
    assert resp.json["message"] == "Password changed successfully"


# ── Test 2: Wrong current password returns 400 ───────────────────────────────


def test_wrong_current_password(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they provide an incorrect current password
    THEN the server responds 400 with 'Current password is incorrect'
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, "wrongpassword", "NewSecure#1")

    assert resp.status_code == 400
    assert resp.json["error"] == "Current password is incorrect"


# ── Test 3: New password too short rejected ───────────────────────────────────


def test_password_too_short_rejected(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they provide a new password shorter than 8 characters
    THEN the server responds 400 with validation failure
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "Ab1")

    assert resp.status_code == 400
    assert "Password validation failed" in resp.json["error"]
    assert "Must be at least 8 characters" in resp.json["failures"]


# ── Test 4: Missing uppercase rejected ────────────────────────────────────────


def test_missing_uppercase_rejected(test_client, db):
    """
    GIVEN an authenticated user
    WHEN their new password has no uppercase letter
    THEN the server responds 400 with the specific failure
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "nouppercase1")

    assert resp.status_code == 400
    assert "Must contain at least one uppercase letter" in resp.json["failures"]


# ── Test 5: Missing lowercase rejected ────────────────────────────────────────


def test_missing_lowercase_rejected(test_client, db):
    """
    GIVEN an authenticated user
    WHEN their new password has no lowercase letter
    THEN the server responds 400 with the specific failure
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "NOLOWERCASE1")

    assert resp.status_code == 400
    assert "Must contain at least one lowercase letter" in resp.json["failures"]


# ── Test 6: Missing number rejected ───────────────────────────────────────────


def test_missing_number_rejected(test_client, db):
    """
    GIVEN an authenticated user
    WHEN their new password has no digit
    THEN the server responds 400 with the specific failure
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "NoNumberHere")

    assert resp.status_code == 400
    assert "Must contain at least one number" in resp.json["failures"]


# ── Test 7: Special characters accepted ───────────────────────────────────────


def test_special_characters_accepted(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they use special characters (!_?#$%^&) in their new password
    THEN the password is accepted (200 success)
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "My!_?#$%^&1a")

    assert resp.status_code == 200
    assert resp.json["message"] == "Password changed successfully"


# ── Test 8: Can login with new password after change ──────────────────────────


def test_can_login_with_new_password(test_client, db):
    """
    GIVEN a user who successfully changed their password
    WHEN they log in with the new password
    THEN login succeeds (200)
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    new_password = "BrandNew#9"
    _change_password(test_client, DEFAULT_PASSWORD, new_password)

    # Logout by clearing cookies (just make a fresh login attempt)
    login_resp = _login(test_client, "user@example.com", new_password)

    assert login_resp.status_code == 200


# ── Test 9: Cannot login with old password after change ───────────────────────


def test_cannot_login_with_old_password(test_client, db):
    """
    GIVEN a user who successfully changed their password
    WHEN they try to log in with the old password
    THEN login fails (401)
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    _change_password(test_client, DEFAULT_PASSWORD, "BrandNew#9")

    # Try logging in with the old password
    login_resp = _login(test_client, "user@example.com", DEFAULT_PASSWORD)

    assert login_resp.status_code == 401


# ── Test 10: Unauthenticated request rejected ─────────────────────────────────


def test_unauthenticated_password_change_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN PUT /user/password is called
    THEN the server responds 401
    """
    resp = _change_password(test_client, "anything", "NewSecure#1")

    assert resp.status_code == 401


# ── Additional edge-case tests ────────────────────────────────────────────────


def test_missing_current_password_field(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they omit the current_password field
    THEN the server responds 400
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = test_client.put(
        "/user/password",
        data=json.dumps({"new_password": "NewSecure#1"}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "Current password is required" in resp.json["error"]


def test_missing_new_password_field(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they omit the new_password field
    THEN the server responds 400
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    resp = test_client.put(
        "/user/password",
        data=json.dumps({"current_password": DEFAULT_PASSWORD}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "New password is required" in resp.json["error"]


def test_teacher_can_change_password(test_client, db):
    """
    GIVEN a teacher user
    WHEN they change their password with valid input
    THEN it succeeds (any role can change password)
    """
    _create_user("Teacher", "teacher@example.com", role="teacher")
    _login(test_client, "teacher@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "TeacherNew#1")

    assert resp.status_code == 200


def test_admin_can_change_password(test_client, db):
    """
    GIVEN an admin user
    WHEN they change their password with valid input
    THEN it succeeds (any role can change password)
    """
    _create_user("Admin", "admin@example.com", role="admin")
    _login(test_client, "admin@example.com")

    resp = _change_password(test_client, DEFAULT_PASSWORD, "AdminNew#1")

    assert resp.status_code == 200


def test_multiple_validation_failures_returned(test_client, db):
    """
    GIVEN an authenticated user
    WHEN their new password fails multiple criteria
    THEN all failure messages are returned in the response
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    # "abc" fails: too short, no uppercase, no number
    resp = _change_password(test_client, DEFAULT_PASSWORD, "abc")

    assert resp.status_code == 400
    failures = resp.json["failures"]
    assert len(failures) >= 3
    assert "Must be at least 8 characters" in failures
    assert "Must contain at least one uppercase letter" in failures
    assert "Must contain at least one number" in failures


def test_password_with_all_special_characters(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they set a password containing all listed special characters
    THEN it is accepted without any being stripped
    """
    _create_user("User", "user@example.com")
    _login(test_client, "user@example.com")

    special_password = "Aa1!_?#$%^&"
    resp = _change_password(test_client, DEFAULT_PASSWORD, special_password)
    assert resp.status_code == 200

    # Verify we can log in with that password
    login_resp = _login(test_client, "user@example.com", special_password)
    assert login_resp.status_code == 200

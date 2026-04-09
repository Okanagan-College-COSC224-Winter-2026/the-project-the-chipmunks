"""
Tests for the notification system.
"""

import json

from werkzeug.security import generate_password_hash

from api.models.db import db as _db
from api.models.user_model import User
from api.models.notification_model import Notification
from api.services.notification_service import create_notification


def _make_student(email="student@test.com", name="Student"):
    """Helper: create a student user directly."""
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(test_client, email, password="password123"):
    """Helper: log in via the auth endpoint."""
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


# ---- 1. Service creates notification correctly ----

def test_create_notification(test_client, db):
    """create_notification service creates a notification with is_read=False."""
    user = _make_student()
    notif = create_notification(
        user_id=user.id,
        type="review_received",
        title="New Review",
        message="Someone reviewed you.",
        link="/student/feedback/1",
    )
    assert notif.id is not None
    assert notif.is_read is False
    assert notif.user_id == user.id
    assert notif.type == "review_received"


# ---- 2. List notifications ----

def test_list_notifications(test_client, db):
    """GET /notification/notifications returns paginated notifications."""
    user = _make_student()
    _login(test_client, user.email)

    create_notification(
        user_id=user.id,
        type="announcement",
        title="Welcome",
        message="Welcome to the app.",
    )

    r = test_client.get("/notification/notifications")
    assert r.status_code == 200
    data = r.json
    assert "notifications" in data
    assert "total" in data
    assert data["total"] >= 1


# ---- 3. Unread count ----

def test_unread_count(test_client, db):
    """GET /notification/notifications/unread-count returns >= 1 after creating a notification."""
    user = _make_student()
    _login(test_client, user.email)

    create_notification(
        user_id=user.id,
        type="grade_posted",
        title="Grade Posted",
        message="Your grade has been posted.",
    )

    r = test_client.get("/notification/notifications/unread-count")
    assert r.status_code == 200
    assert r.json["unread_count"] >= 1


# ---- 4. Mark single read ----

def test_mark_single_read(test_client, db):
    """PUT /notification/notifications/<id>/read marks notification as read."""
    user = _make_student()
    _login(test_client, user.email)

    notif = create_notification(
        user_id=user.id,
        type="feedback_received",
        title="Feedback",
        message="You received feedback.",
    )

    r = test_client.put(f"/notification/notifications/{notif.id}/read")
    assert r.status_code == 200

    updated = _db.session.get(Notification, notif.id)
    assert updated.is_read is True


# ---- 5. Mark all read ----

def test_mark_all_read(test_client, db):
    """PUT /notification/notifications/read-all marks all as read."""
    user = _make_student()
    _login(test_client, user.email)

    create_notification(
        user_id=user.id,
        type="review_assigned",
        title="Review Assigned",
        message="You have a new review to complete.",
    )
    create_notification(
        user_id=user.id,
        type="account_update",
        title="Account Updated",
        message="Your account was updated.",
    )

    r = test_client.put("/notification/notifications/read-all")
    assert r.status_code == 200

    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    assert unread == 0

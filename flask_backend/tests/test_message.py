"""
Tests for Task 1 — In-Group Student Messaging
GET  /message/group/<group_id>       — fetch messages
POST /message/group/<group_id>       — send a message
PUT  /message/group/<group_id>/read  — mark messages as read

Sprint-plan test cases:
    1. GET returns 200 with messages for an authorized group member
    2. GET returns 403 for a non-member
    3. POST creates a message and returns 201
    4. POST returns 400 when content is empty
    + Additional edge-case tests
"""

import json

import pytest
from werkzeug.security import generate_password_hash

from api.models import Assignment, Course, CourseGroup, Group_Members, User
from api.models.db import db as _db
from api.models.message_model import Message

DEFAULT_PASSWORD = "password123"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_user(name, email, role="student", password=DEFAULT_PASSWORD):
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
    """Log in via the cookie-based auth endpoint (sets JWT cookie)."""
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _seed_group(member_emails: list[str]) -> tuple:
    """
    Create: teacher → course → assignment → CourseGroup,
    then enroll all users as Group_Members.
    Returns (assignment, group, [users...]).
    """
    teacher = _create_user("Teacher", "teacher_msg@test.com", role="teacher")

    course = Course(teacherID=teacher.id, name="Messaging Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Assignment 1", rubric_text="R")
    _db.session.add(assignment)
    _db.session.commit()

    group = CourseGroup(name="Group A", assignmentID=assignment.id)
    _db.session.add(group)
    _db.session.commit()

    users = []
    for i, email in enumerate(member_emails):
        u = _create_user(f"Student {i+1}", email)
        users.append(u)
        membership = Group_Members(userID=u.id, groupID=group.id, assignmentID=assignment.id)
        _db.session.add(membership)
    _db.session.commit()

    return assignment, group, users


# ── Test 1: GET returns 200 for a group member ────────────────────────────────

def test_get_messages_authorized_member(test_client, db):
    """
    GIVEN a student who is a member of the group
    WHEN  GET /message/group/<id>
    THEN  200 and response is a list
    """
    _assignment, group, users = _seed_group(["member1@test.com", "member2@test.com"])
    _login(test_client, "member1@test.com")

    resp = test_client.get(f"/message/group/{group.id}")

    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


# ── Test 2: GET returns 403 for a non-member ──────────────────────────────────

def test_get_messages_non_member_forbidden(test_client, db):
    """
    GIVEN a student who is NOT a member of the group
    WHEN  GET /message/group/<id>
    THEN  403 Forbidden
    """
    _assignment, group, _users = _seed_group(["member1@test.com"])
    outsider = _create_user("Outsider", "outsider@test.com")
    _login(test_client, "outsider@test.com")

    resp = test_client.get(f"/message/group/{group.id}")

    assert resp.status_code == 403
    assert "error" in resp.get_json()


# ── Test 3: POST creates a message and returns 201 ────────────────────────────

def test_post_message_creates_and_returns_201(test_client, db):
    """
    GIVEN an authenticated group member
    WHEN  POST /message/group/<id> with valid content
    THEN  201 and the message is persisted with correct fields
    """
    _assignment, group, users = _seed_group(["sender@test.com"])
    _login(test_client, "sender@test.com")

    resp = test_client.post(
        f"/message/group/{group.id}",
        data=json.dumps({"content": "Hello group!"}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["content"] == "Hello group!"
    assert data["sender_id"] == users[0].id
    assert data["group_id"] == group.id

    # Confirm persisted in DB
    assert Message.query.filter_by(groupID=group.id).count() == 1


# ── Test 4: POST returns 400 for empty content ────────────────────────────────

def test_post_message_empty_content_returns_400(test_client, db):
    """
    GIVEN an authenticated group member
    WHEN  POST /message/group/<id> with empty content
    THEN  400 Bad Request
    """
    _assignment, group, _users = _seed_group(["sender@test.com"])
    _login(test_client, "sender@test.com")

    resp = test_client.post(
        f"/message/group/{group.id}",
        data=json.dumps({"content": "   "}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ── Additional edge-case tests ────────────────────────────────────────────────

def test_post_message_missing_content_field_returns_400(test_client, db):
    """
    GIVEN an authenticated group member
    WHEN  POST /message/group/<id> with no content key
    THEN  400 Bad Request
    """
    _assignment, group, _users = _seed_group(["sender@test.com"])
    _login(test_client, "sender@test.com")

    resp = test_client.post(
        f"/message/group/{group.id}",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400


def test_get_messages_returns_correct_order(test_client, db):
    """
    GIVEN two messages sent in sequence
    WHEN  GET /message/group/<id>
    THEN  messages are returned oldest-first
    """
    _assignment, group, users = _seed_group(["member@test.com"])
    _login(test_client, "member@test.com")

    msg1 = Message(groupID=group.id, senderID=users[0].id, content="First")
    msg2 = Message(groupID=group.id, senderID=users[0].id, content="Second")
    _db.session.add(msg1)
    _db.session.add(msg2)
    _db.session.commit()

    resp = test_client.get(f"/message/group/{group.id}")

    assert resp.status_code == 200
    messages = resp.get_json()
    assert len(messages) == 2
    assert messages[0]["content"] == "First"
    assert messages[1]["content"] == "Second"


def test_get_messages_includes_sender_name(test_client, db):
    """
    GIVEN a message sent by a named user
    WHEN  GET /message/group/<id>
    THEN  each message includes the sender_name field
    """
    _assignment, group, users = _seed_group(["member@test.com"])

    msg = Message(groupID=group.id, senderID=users[0].id, content="Hi")
    _db.session.add(msg)
    _db.session.commit()

    _login(test_client, "member@test.com")
    resp = test_client.get(f"/message/group/{group.id}")

    assert resp.status_code == 200
    item = resp.get_json()[0]
    assert item["sender_name"] == "Student 1"


def test_post_message_non_member_forbidden(test_client, db):
    """
    GIVEN a user who is NOT in the group
    WHEN  POST /message/group/<id>
    THEN  403 Forbidden — non-members cannot send messages
    """
    _assignment, group, _users = _seed_group(["member@test.com"])
    _create_user("Outsider", "outsider@test.com")
    _login(test_client, "outsider@test.com")

    resp = test_client.post(
        f"/message/group/{group.id}",
        data=json.dumps({"content": "Sneaky message"}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 403


def test_mark_read_marks_others_messages(test_client, db):
    """
    GIVEN two members, member2 has sent a message
    WHEN  member1 calls PUT /message/group/<id>/read
    THEN  200 and member2's message is marked as read
    """
    _assignment, group, users = _seed_group(["member1@test.com", "member2@test.com"])
    member1, member2 = users[0], users[1]

    msg = Message(groupID=group.id, senderID=member2.id, content="Hey!")
    _db.session.add(msg)
    _db.session.commit()

    _login(test_client, "member1@test.com")
    resp = test_client.put(f"/message/group/{group.id}/read")

    assert resp.status_code == 200

    _db.session.refresh(msg)
    assert msg.is_read is True


def test_mark_read_does_not_mark_own_messages(test_client, db):
    """
    GIVEN a member who has sent their own messages
    WHEN  they call PUT /message/group/<id>/read
    THEN  their own messages remain unread
    """
    _assignment, group, users = _seed_group(["member1@test.com"])
    member1 = users[0]

    own_msg = Message(groupID=group.id, senderID=member1.id, content="My message")
    _db.session.add(own_msg)
    _db.session.commit()

    _login(test_client, "member1@test.com")
    test_client.put(f"/message/group/{group.id}/read")

    _db.session.refresh(own_msg)
    assert own_msg.is_read is False


def test_unauthenticated_get_returns_401(test_client, db):
    """
    GIVEN no logged-in user
    WHEN  GET /message/group/1
    THEN  401 Unauthorized
    """
    resp = test_client.get("/message/group/1")
    assert resp.status_code == 401


def test_unauthenticated_post_returns_401(test_client, db):
    """
    GIVEN no logged-in user
    WHEN  POST /message/group/1
    THEN  401 Unauthorized
    """
    resp = test_client.post(
        "/message/group/1",
        data=json.dumps({"content": "test"}),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 401


def test_get_messages_response_shape(test_client, db):
    """
    GIVEN a group with one message
    WHEN  GET /message/group/<id>
    THEN  each item has exactly the keys the frontend expects
    """
    _assignment, group, users = _seed_group(["member@test.com"])

    msg = Message(groupID=group.id, senderID=users[0].id, content="Shape test")
    _db.session.add(msg)
    _db.session.commit()

    _login(test_client, "member@test.com")
    resp = test_client.get(f"/message/group/{group.id}")

    assert resp.status_code == 200
    item = resp.get_json()[0]
    expected_keys = {"id", "group_id", "sender_id", "sender_name",
                     "content", "created_at", "is_read"}
    assert set(item.keys()) == expected_keys
"""
Tests for the Advanced Rubric Builder endpoints.
"""

import json

from werkzeug.security import generate_password_hash

from api.models.db import db as _db
from api.models.user_model import User
from api.models.course_model import Course
from api.models.assignment_model import Assignment
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription


# ---- helpers ----

def _make_teacher(email="teacher@test.com", name="Teacher"):
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(test_client, email, password="password123"):
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _make_course(teacher_id, name="Test Course"):
    course = Course(teacherID=teacher_id, name=name)
    _db.session.add(course)
    _db.session.commit()
    return course


def _make_assignment(course_id, name="Test Assignment"):
    assignment = Assignment(courseID=course_id, name=name, rubric_text="")
    _db.session.add(assignment)
    _db.session.commit()
    return assignment


def _two_criteria_payload(name="My Rubric"):
    return {
        "name": name,
        "criteria": [
            {
                "name": "Quality",
                "description": "Quality of work",
                "max_score": 10,
                "weight": 60,
                "position": 0,
            },
            {
                "name": "Effort",
                "description": "Effort put in",
                "max_score": 10,
                "weight": 40,
                "position": 1,
            },
        ],
    }


# ---- 1. GET rubric when none exists ----

def test_get_rubric_empty(test_client, db):
    """GET rubric for nonexistent assignment returns 200 with rubric: None."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)

    r = test_client.get("/rubric-builder/assignment/9999/rubric")
    assert r.status_code == 200
    assert r.json["rubric"] is None


# ---- 2. Create rubric with 2 criteria ----

def test_create_rubric(test_client, db):
    """PUT creates rubric with 2 criteria (weights summing to 100)."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)
    course = _make_course(teacher.id)
    assignment = _make_assignment(course.id)

    payload = _two_criteria_payload()
    r = test_client.put(
        f"/rubric-builder/assignment/{assignment.id}/rubric",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    data = r.json["rubric"]
    assert len(data["criteria"]) == 2
    assert data["name"] == "My Rubric"


# ---- 3. Weights must sum to 100 ----

def test_weights_must_sum_100(test_client, db):
    """PUT with weights summing to 60 returns 400."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)
    course = _make_course(teacher.id)
    assignment = _make_assignment(course.id)

    payload = {
        "name": "Bad Rubric",
        "criteria": [
            {"name": "A", "description": "", "max_score": 10, "weight": 30, "position": 0},
            {"name": "B", "description": "", "max_score": 10, "weight": 30, "position": 1},
        ],
    }
    r = test_client.put(
        f"/rubric-builder/assignment/{assignment.id}/rubric",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


# ---- 4. Reorder criteria ----

def test_reorder_criteria(test_client, db):
    """PUT reorder with reversed ID list returns 200."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)
    course = _make_course(teacher.id)
    assignment = _make_assignment(course.id)

    # Create rubric first
    payload = _two_criteria_payload()
    r = test_client.put(
        f"/rubric-builder/assignment/{assignment.id}/rubric",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    rubric_data = r.json["rubric"]
    rubric_id = rubric_data["id"]
    criteria_ids = [c["id"] for c in rubric_data["criteria"]]

    # Reverse order
    reversed_ids = list(reversed(criteria_ids))
    r = test_client.put(
        f"/rubric-builder/rubric/{rubric_id}/reorder",
        data=json.dumps({"order": reversed_ids}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json["message"] == "Reordered"


# ---- 5. Save and list templates ----

def test_save_and_list_templates(test_client, db):
    """PUT with is_template: True, then GET /templates returns at least 1."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)
    course = _make_course(teacher.id)
    assignment = _make_assignment(course.id)

    payload = _two_criteria_payload("Template Rubric")
    payload["is_template"] = True
    r = test_client.put(
        f"/rubric-builder/assignment/{assignment.id}/rubric",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200

    r = test_client.get("/rubric-builder/templates")
    assert r.status_code == 200
    assert len(r.json["templates"]) >= 1


# ---- 6. Apply template to another assignment ----

def test_apply_template(test_client, db):
    """POST apply template to another assignment returns 201 with criteria copied."""
    teacher = _make_teacher()
    _login(test_client, teacher.email)
    course = _make_course(teacher.id)
    assignment1 = _make_assignment(course.id, "Assignment 1")
    assignment2 = _make_assignment(course.id, "Assignment 2")

    # Create template on assignment1
    payload = _two_criteria_payload("Template")
    payload["is_template"] = True
    r = test_client.put(
        f"/rubric-builder/assignment/{assignment1.id}/rubric",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    template_id = r.json["rubric"]["id"]

    # Apply to assignment2
    r = test_client.post(f"/rubric-builder/templates/{template_id}/apply/{assignment2.id}")
    assert r.status_code == 201
    data = r.json["rubric"]
    assert len(data["criteria"]) == 2
    assert data["assignment_id"] == assignment2.id

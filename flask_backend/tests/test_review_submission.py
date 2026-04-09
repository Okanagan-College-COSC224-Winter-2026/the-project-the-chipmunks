"""
Tests for US1/US11 - Rubric-Based Peer Review Submission.
POST /api/reviews/submit
GET /assignment/<assignment_id>/rubric
"""

import json
import pytest
from werkzeug.security import generate_password_hash

from api.models import User, Course, Assignment, Review, Criterion, User_Course, Group_Members, CourseGroup
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription
from api.models.db import db as _db


# ============================================================
# HELPERS
# ============================================================

def login_as(test_client, email, password="password"):
    """Log in a user via the auth endpoint (sets session cookie)."""
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def create_user(name, email, role="student"):
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash("password"),
        role=role,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def create_course(teacher_id, name="Test Course"):
    course = Course(teacherID=teacher_id, name=name)
    _db.session.add(course)
    _db.session.commit()
    return course


def create_assignment_with_rubric(course_id, name="Assignment 1", score_max=5):
    assignment = Assignment(courseID=course_id, name=name, rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    crit_desc = CriteriaDescription(
        rubricID=rubric.id,
        question="Quality of work",
        scoreMax=score_max,
        hasScore=True,
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    return assignment, rubric, crit_desc


def setup_group(assignment_id, reviewer_id, reviewee_id):
    """Put reviewer and reviewee in the same group."""
    group = CourseGroup(name="Group 1", assignmentID=assignment_id)
    _db.session.add(group)
    _db.session.commit()

    _db.session.add(Group_Members(userID=reviewer_id, groupID=group.id, assignmentID=assignment_id))
    _db.session.add(Group_Members(userID=reviewee_id, groupID=group.id, assignmentID=assignment_id))
    _db.session.commit()
    return group


# ============================================================
# TESTS
# ============================================================

def test_submit_review_success(test_client, db):
    """
    GIVEN a valid reviewer, reviewee, and assignment with rubric
    WHEN POST /api/reviews/submit is called with valid data
    THEN return 201 with review_id
    """
    teacher = create_user("Teacher", "teacher@example.com", role="teacher")
    reviewer = create_user("Reviewer", "reviewer@example.com")
    reviewee = create_user("Reviewee", "reviewee@example.com")

    course = create_course(teacher.id)
    User_Course.add(reviewer.id, course.id)
    User_Course.add(reviewee.id, course.id)
    assignment, rubric, crit_desc = create_assignment_with_rubric(course.id)

    login_as(test_client, "reviewer@example.com")

    resp = test_client.post(
        "/api/reviews/submit",
        data=json.dumps({
            "assignment_id": assignment.id,
            "reviewee_id": reviewee.id,
            "criteria": [
                {
                    "criteria_description_id": crit_desc.id,
                    "grade": 4,
                    "comments": "Good work!",
                }
            ],
        }),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert "review_id" in data


def test_submit_review_duplicate(test_client, db):
    """
    GIVEN a reviewer who already submitted a review for a reviewee
    WHEN POST /api/reviews/submit is called again
    THEN return 409 conflict
    """
    teacher = create_user("Teacher", "teacher@example.com", role="teacher")
    reviewer = create_user("Reviewer", "reviewer@example.com")
    reviewee = create_user("Reviewee", "reviewee@example.com")

    course = create_course(teacher.id)
    assignment, rubric, crit_desc = create_assignment_with_rubric(course.id)

    login_as(test_client, "reviewer@example.com")

    payload = json.dumps({
        "assignment_id": assignment.id,
        "reviewee_id": reviewee.id,
        "criteria": [{"criteria_description_id": crit_desc.id, "grade": 3, "comments": ""}],
    })
    headers = {"Content-Type": "application/json"}

    resp1 = test_client.post("/api/reviews/submit", data=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = test_client.post("/api/reviews/submit", data=payload, headers=headers)
    assert resp2.status_code == 409


def test_submit_review_self(test_client, db):
    """
    GIVEN a student trying to review themselves
    WHEN POST /api/reviews/submit is called with reviewer == reviewee
    THEN return 400
    """
    teacher = create_user("Teacher", "teacher@example.com", role="teacher")
    student = create_user("Student", "student@example.com")

    course = create_course(teacher.id)
    assignment, rubric, crit_desc = create_assignment_with_rubric(course.id)

    login_as(test_client, "student@example.com")

    resp = test_client.post(
        "/api/reviews/submit",
        data=json.dumps({
            "assignment_id": assignment.id,
            "reviewee_id": student.id,
            "criteria": [{"criteria_description_id": crit_desc.id, "grade": 5, "comments": ""}],
        }),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400


def test_submit_review_unauthenticated(test_client, db):
    """
    GIVEN no user is logged in
    WHEN POST /api/reviews/submit is called
    THEN return 401
    """
    resp = test_client.post(
        "/api/reviews/submit",
        data=json.dumps({
            "assignment_id": 1,
            "reviewee_id": 1,
            "criteria": [],
        }),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 401


def test_get_rubric_success(test_client, db):
    """
    GIVEN an assignment with a rubric and criteria
    WHEN GET /assignment/<assignment_id>/rubric is called
    THEN return 200 with rubric data including criteria
    """
    teacher = create_user("Teacher", "teacher@example.com", role="teacher")
    student = create_user("Student", "student@example.com")

    course = create_course(teacher.id)
    assignment, rubric, crit_desc = create_assignment_with_rubric(course.id)

    login_as(test_client, "student@example.com")

    resp = test_client.get(f"/assignment/{assignment.id}/rubric")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["rubric_id"] == rubric.id
    assert data["assignment_id"] == assignment.id
    assert len(data["criteria"]) == 1
    assert data["criteria"][0]["question"] == "Quality of work"
    assert data["criteria"][0]["score_max"] == 5


def test_get_rubric_not_found(test_client, db):
    """
    GIVEN an invalid assignment ID
    WHEN GET /assignment/<assignment_id>/rubric is called
    THEN return 404
    """
    student = create_user("Student", "student@example.com")
    login_as(test_client, "student@example.com")

    resp = test_client.get("/assignment/999999/rubric")

    assert resp.status_code == 404

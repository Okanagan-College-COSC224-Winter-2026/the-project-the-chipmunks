"""
Tests for US12 - Student Feedback Viewing endpoint.
GET /student/assignments/<assignment_id>/feedback
Follows the same pattern as test_student_grades.py (Dev 3 / Ayman).
"""

import json
import pytest
from werkzeug.security import generate_password_hash

from api.models import User, Course, Assignment, Review, Criterion, User_Course
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


def create_teacher(email="teacher@example.com"):
    teacher = User(
        name="Teacher",
        email=email,
        hash_pass=generate_password_hash("password"),
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()
    return teacher


def create_student(name="Student One", email="student@example.com"):
    student = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash("password"),
        role="student",
    )
    _db.session.add(student)
    _db.session.commit()
    return student


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


def create_review(assignment_id, reviewer_id, reviewee_id, crit_desc_id, grade, comment="Test comment"):
    review = Review(
        assignmentID=assignment_id,
        reviewerID=reviewer_id,
        revieweeID=reviewee_id,
    )
    _db.session.add(review)
    _db.session.commit()

    criterion = Criterion(
        reviewID=review.id,
        criterionRowID=crit_desc_id,
        grade=grade,
        comments=comment,
    )
    _db.session.add(criterion)
    _db.session.commit()
    return review


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def setup_teacher(db):
    return create_teacher("teacher@example.com")


@pytest.fixture
def setup_student(db):
    return create_student("Student One", "student@example.com")


@pytest.fixture
def setup_reviewer(db):
    return create_student("Reviewer One", "reviewer@example.com")


# ============================================================
# TESTS
# ============================================================

def test_feedback_no_reviews(test_client, db, setup_teacher, setup_student):
    """
    GIVEN a student with no reviews received
    WHEN GET /student/assignments/<id>/feedback is called
    THEN return 200 with empty criteria list
    """
    teacher = setup_teacher
    student = setup_student

    course = create_course(teacher.id)
    User_Course.add(student.id, course.id)
    assignment, _, _ = create_assignment_with_rubric(course.id)

    login_as(test_client, "student@example.com")

    resp = test_client.get(f"/student/assignments/{assignment.id}/feedback")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["assignment_id"] == assignment.id
    assert data["total_reviews"] == 0
    assert data["criteria_feedback"] == []


def test_feedback_with_reviews(test_client, db, setup_teacher, setup_student, setup_reviewer):
    """
    GIVEN a student with 2 peer reviews received
    WHEN GET /student/assignments/<id>/feedback is called
    THEN return 200 with aggregated scores and comments
    """
    teacher = setup_teacher
    student = setup_student
    reviewer = setup_reviewer

    course = create_course(teacher.id)
    User_Course.add(student.id, course.id)
    assignment, _, crit_desc = create_assignment_with_rubric(course.id, score_max=5)

    create_review(assignment.id, reviewer.id, student.id, crit_desc.id, 4, "Good explanation.")
    create_review(assignment.id, reviewer.id, student.id, crit_desc.id, 2, "Could be clearer.")

    login_as(test_client, "student@example.com")

    resp = test_client.get(f"/student/assignments/{assignment.id}/feedback")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_reviews"] == 2
    assert len(data["criteria_feedback"]) == 1

    crit = data["criteria_feedback"][0]
    assert crit["avg_score"] == 3.0  # (4 + 2) / 2
    assert crit["max_score"] == 5
    assert len(crit["comments"]) == 2


def test_feedback_reviewer_identity_hidden(test_client, db, setup_teacher, setup_student, setup_reviewer):
    """
    GIVEN a student with a peer review received
    WHEN GET /student/assignments/<id>/feedback is called
    THEN reviewer email and ID must NOT appear in the response
    """
    teacher = setup_teacher
    student = setup_student
    reviewer = setup_reviewer

    course = create_course(teacher.id)
    User_Course.add(student.id, course.id)
    assignment, _, crit_desc = create_assignment_with_rubric(course.id)

    create_review(assignment.id, reviewer.id, student.id, crit_desc.id, 4, "Nice work.")

    login_as(test_client, "student@example.com")

    resp = test_client.get(f"/student/assignments/{assignment.id}/feedback")

    assert resp.status_code == 200
    response_text = resp.get_data(as_text=True)
    assert reviewer.email not in response_text
    assert str(reviewer.id) not in response_text


def test_feedback_unauthenticated(test_client, db, setup_teacher):
    """
    GIVEN no user is logged in
    WHEN GET /student/assignments/<id>/feedback is called
    THEN return 401
    """
    teacher = setup_teacher
    course = create_course(teacher.id)
    assignment, _, _ = create_assignment_with_rubric(course.id)

    resp = test_client.get(f"/student/assignments/{assignment.id}/feedback")
    assert resp.status_code == 401


def test_feedback_assignment_not_found(test_client, db, setup_student):
    """
    GIVEN a logged-in student
    WHEN GET /student/assignments/999999/feedback is called
    THEN return 404
    """
    login_as(test_client, "student@example.com")

    resp = test_client.get("/student/assignments/999999/feedback")
    assert resp.status_code == 404


# Alias tests matching the sprint plan naming convention
test_get_feedback_success = test_feedback_with_reviews
test_get_feedback_no_reviews = test_feedback_no_reviews
test_get_feedback_unauthenticated = test_feedback_unauthenticated
test_feedback_anonymity = test_feedback_reviewer_identity_hidden


def test_feedback_score_aggregation(test_client, db, setup_teacher, setup_student):
    """
    GIVEN a student with 3 reviews from different reviewers
    WHEN GET /student/assignments/<id>/feedback is called
    THEN the average score is correctly calculated across all 3 reviews
    """
    teacher = setup_teacher
    student = setup_student

    reviewer1 = create_student("Reviewer A", "reviewerA@example.com")
    reviewer2 = create_student("Reviewer B", "reviewerB@example.com")
    reviewer3 = create_student("Reviewer C", "reviewerC@example.com")

    course = create_course(teacher.id)
    User_Course.add(student.id, course.id)
    assignment, _, crit_desc = create_assignment_with_rubric(course.id, score_max=10)

    create_review(assignment.id, reviewer1.id, student.id, crit_desc.id, 8, "Great")
    create_review(assignment.id, reviewer2.id, student.id, crit_desc.id, 6, "Good")
    create_review(assignment.id, reviewer3.id, student.id, crit_desc.id, 7, "Nice")

    login_as(test_client, "student@example.com")

    resp = test_client.get(f"/student/assignments/{assignment.id}/feedback")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_reviews"] == 3
    assert len(data["criteria_feedback"]) == 1

    crit = data["criteria_feedback"][0]
    assert crit["avg_score"] == 7.0  # (8 + 6 + 7) / 3
    assert crit["max_score"] == 10
    assert len(crit["comments"]) == 3

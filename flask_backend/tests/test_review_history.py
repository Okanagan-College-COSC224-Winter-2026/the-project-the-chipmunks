"""
Tests for Task 3 Sprint 5 — Student Peer Review History & Comparison
GET /review-history/my-reviews
GET /review-history/my-trends

Test cases:
    1.  my_reviews returns empty given/received lists when student has no reviews
    2.  my_reviews returns correct given and received data when reviews exist
    3.  my_trends returns empty trend/comparison when student has no reviews
    4.  my_trends returns correct my_avg and class_avg when reviews exist
    + Additional edge-case tests
"""

import json

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    Criterion,
    CriteriaDescription,
    Review,
    Rubric,
    User,
)
from api.models.db import db as _db


# ── Helpers ───────────────────────────────────────────────────────────────────

DEFAULT_PASSWORD = "password123"


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


def _seed_world(student_email="student@test.com"):
    """
    Create a minimal world:
        teacher → course → assignment → rubric → criteria_description
        student (reviewee) + peer (reviewer)
        one review with one graded criterion

    Returns (student, peer, assignment, review, crit_desc).
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    student = _create_user("Student One", student_email)
    peer    = _create_user("Peer Student", "peer@test.com")

    course = Course(teacherID=teacher.id, name="Test Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Assignment 1", rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    crit_desc = CriteriaDescription(
        rubricID=rubric.id, question="Quality", scoreMax=10, hasScore=True
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    # peer reviews student (peer=reviewer, student=reviewee)
    review = Review(
        assignmentID=assignment.id,
        reviewerID=peer.id,
        revieweeID=student.id,
    )
    _db.session.add(review)
    _db.session.commit()

    criterion = Criterion(
        reviewID=review.id,
        criterionRowID=crit_desc.id,
        grade=8,
        comments="Good work",
    )
    _db.session.add(criterion)
    _db.session.commit()

    return student, peer, assignment, review, crit_desc


# ── Test 1: my_reviews empty ──────────────────────────────────────────────────

def test_my_reviews_empty(test_client, db):
    """
    GIVEN a student with no reviews
    WHEN  GET /review-history/my-reviews
    THEN  200 with empty given and received lists
    """
    _create_user("Student", "student@test.com")
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-reviews")

    assert resp.status_code == 200
    data = resp.get_json()
    assert "given" in data
    assert "received" in data
    assert data["given"] == []
    assert data["received"] == []


# ── Test 2: my_reviews with data ──────────────────────────────────────────────

def test_my_reviews_with_data(test_client, db):
    """
    GIVEN a student who has received a review
    WHEN  GET /review-history/my-reviews
    THEN  200 and received list contains the review with correct fields
    """
    student, peer, assignment, review, _ = _seed_world()
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-reviews")

    assert resp.status_code == 200
    data = resp.get_json()

    # Student received one review
    assert len(data["received"]) == 1
    item = data["received"][0]
    assert item["id"] == review.id
    assert item["assignment_id"] == assignment.id
    assert item["assignment_name"] == "Assignment 1"
    assert item["other_student"] == "Peer Student"
    assert item["role"] == "received"
    assert item["score"] == 8.0   # avg of [8]


def test_my_reviews_given_role(test_client, db):
    """
    GIVEN a student who gave a review to a peer
    WHEN  GET /review-history/my-reviews
    THEN  given list contains the review with role='given' and correct other_student
    """
    student, peer, assignment, _review, crit_desc = _seed_world()

    # Now student also gives a review to peer
    given_review = Review(
        assignmentID=assignment.id,
        reviewerID=student.id,
        revieweeID=peer.id,
    )
    _db.session.add(given_review)
    _db.session.commit()

    criterion = Criterion(
        reviewID=given_review.id,
        criterionRowID=crit_desc.id,
        grade=7,
        comments="Decent",
    )
    _db.session.add(criterion)
    _db.session.commit()

    _login(test_client, "student@test.com")
    resp = test_client.get("/review-history/my-reviews")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["given"]) == 1
    item = data["given"][0]
    assert item["role"] == "given"
    assert item["other_student"] == "Peer Student"
    assert item["score"] == 7.0


# ── Test 3: my_trends empty ───────────────────────────────────────────────────

def test_my_trends_empty(test_client, db):
    """
    GIVEN a student with no reviews received
    WHEN  GET /review-history/my-trends
    THEN  200 with empty trend and comparison lists
    """
    _create_user("Student", "student@test.com")
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-trends")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["trend"] == []
    assert data["comparison"] == []


# ── Test 4: my_trends with data ───────────────────────────────────────────────

def test_my_trends_with_data(test_client, db):
    """
    GIVEN a student who has received a graded review
    WHEN  GET /review-history/my-trends
    THEN  200 and trend contains my_avg, comparison contains class_avg
    """
    student, _peer, assignment, _review, _ = _seed_world()
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-trends")

    assert resp.status_code == 200
    data = resp.get_json()

    assert len(data["trend"]) == 1
    trend_item = data["trend"][0]
    assert trend_item["assignment_id"] == assignment.id
    assert trend_item["assignment_name"] == "Assignment 1"
    assert trend_item["my_avg"] == 8.0
    assert trend_item["review_count"] == 1

    assert len(data["comparison"]) == 1
    comp_item = data["comparison"][0]
    assert comp_item["assignment_name"] == "Assignment 1"
    assert comp_item["my_avg"] == 8.0
    assert comp_item["class_avg"] == 8.0   # only one review in class too


# ── Additional edge-case tests ────────────────────────────────────────────────

def test_my_reviews_score_is_avg_of_criteria(test_client, db):
    """
    GIVEN a review with multiple criteria grades (6 and 8)
    WHEN  GET /review-history/my-reviews
    THEN  score is the average (7.0), not the sum
    """
    student, _peer, assignment, review, crit_desc = _seed_world()

    # Add a second criterion with grade 6 (first is already 8)
    crit_desc2 = CriteriaDescription(
        rubricID=crit_desc.rubricID, question="Effort", scoreMax=10, hasScore=True
    )
    _db.session.add(crit_desc2)
    _db.session.commit()

    criterion2 = Criterion(
        reviewID=review.id,
        criterionRowID=crit_desc2.id,
        grade=6,
        comments="OK",
    )
    _db.session.add(criterion2)
    _db.session.commit()

    _login(test_client, "student@test.com")
    resp = test_client.get("/review-history/my-reviews")

    assert resp.status_code == 200
    item = resp.get_json()["received"][0]
    assert item["score"] == 7.0   # avg(8, 6)


def test_my_reviews_score_null_when_no_grades(test_client, db):
    """
    GIVEN a review with a criterion that has grade=None
    WHEN  GET /review-history/my-reviews
    THEN  score is null
    """
    teacher  = _create_user("Teacher2", "teacher2@test.com", role="teacher")
    student  = _create_user("Student", "student@test.com")
    peer     = _create_user("Peer", "peer2@test.com")

    course = Course(teacherID=teacher.id, name="Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Asgn", rubric_text="R")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=False)
    _db.session.add(rubric)
    _db.session.commit()

    crit_desc = CriteriaDescription(
        rubricID=rubric.id, question="Q", scoreMax=5, hasScore=False
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    review = Review(assignmentID=assignment.id, reviewerID=peer.id, revieweeID=student.id)
    _db.session.add(review)
    _db.session.commit()

    # grade is None — comment-only criterion
    criterion = Criterion(reviewID=review.id, criterionRowID=crit_desc.id, grade=None, comments="Nice")
    _db.session.add(criterion)
    _db.session.commit()

    _login(test_client, "student@test.com")
    resp = test_client.get("/review-history/my-reviews")

    assert resp.status_code == 200
    assert resp.get_json()["received"][0]["score"] is None


def test_my_trends_class_avg_includes_all_students(test_client, db):
    """
    GIVEN two students both received reviews on the same assignment (grades 8 and 4)
    WHEN  the first student calls GET /review-history/my-trends
    THEN  class_avg reflects both students' grades (avg = 6.0)
    """
    teacher   = _create_user("Teacher", "teacher@test.com", role="teacher")
    student1  = _create_user("Student One", "student@test.com")
    student2  = _create_user("Student Two", "student2@test.com")
    peer      = _create_user("Peer", "peer@test.com")

    course = Course(teacherID=teacher.id, name="Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Shared Assignment", rubric_text="R")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    crit_desc = CriteriaDescription(
        rubricID=rubric.id, question="Quality", scoreMax=10, hasScore=True
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    # Review for student1 — grade 8
    r1 = Review(assignmentID=assignment.id, reviewerID=peer.id, revieweeID=student1.id)
    _db.session.add(r1)
    _db.session.commit()
    _db.session.add(Criterion(reviewID=r1.id, criterionRowID=crit_desc.id, grade=8))
    _db.session.commit()

    # Review for student2 — grade 4
    r2 = Review(assignmentID=assignment.id, reviewerID=peer.id, revieweeID=student2.id)
    _db.session.add(r2)
    _db.session.commit()
    _db.session.add(Criterion(reviewID=r2.id, criterionRowID=crit_desc.id, grade=4))
    _db.session.commit()

    _login(test_client, "student@test.com")
    resp = test_client.get("/review-history/my-trends")

    assert resp.status_code == 200
    comp = resp.get_json()["comparison"]
    assert len(comp) == 1
    assert comp[0]["my_avg"] == 8.0
    assert comp[0]["class_avg"] == 6.0   # avg(8, 4)


def test_unauthenticated_my_reviews_returns_401(test_client, db):
    """
    GIVEN no logged-in user
    WHEN  GET /review-history/my-reviews
    THEN  401
    """
    resp = test_client.get("/review-history/my-reviews")
    assert resp.status_code == 401


def test_unauthenticated_my_trends_returns_401(test_client, db):
    """
    GIVEN no logged-in user
    WHEN  GET /review-history/my-trends
    THEN  401
    """
    resp = test_client.get("/review-history/my-trends")
    assert resp.status_code == 401


def test_my_reviews_response_shape(test_client, db):
    """
    GIVEN a student with a received review
    WHEN  GET /review-history/my-reviews
    THEN  every item has the exact keys the frontend expects
    """
    _seed_world()
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-reviews")
    assert resp.status_code == 200
    data = resp.get_json()

    expected_keys = {"id", "assignment_id", "assignment_name", "other_student",
                     "score", "role", "created_at"}
    for item in data["received"]:
        assert set(item.keys()) == expected_keys
    for item in data["given"]:
        assert set(item.keys()) == expected_keys


def test_my_trends_response_shape(test_client, db):
    """
    GIVEN a student with a received review
    WHEN  GET /review-history/my-trends
    THEN  trend and comparison items have the exact keys the frontend expects
    """
    _seed_world()
    _login(test_client, "student@test.com")

    resp = test_client.get("/review-history/my-trends")
    assert resp.status_code == 200
    data = resp.get_json()

    for item in data["trend"]:
        assert {"assignment_id", "assignment_name", "my_avg", "review_count"} == set(item.keys())
    for item in data["comparison"]:
        assert {"assignment_name", "my_avg", "class_avg"} == set(item.keys())

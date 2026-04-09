"""
Tests for US7/US8 Extension — Teacher Assignment Analytics Dashboard

Endpoints:
    GET /teacher/assignments/<id>/analytics
    GET /teacher/assignments/<id>/export

Test cases:
    1. analytics returns correct structure (200)
    2. analytics empty assignment returns 200 with completion_pct = 0
    3. analytics forbidden for student (403)
    4. CSV export has correct header row (200)
    5. analytics completion rate is calculated correctly
    6. analytics outlier detection flags reviews beyond 2σ
    7. CSV export forbidden for student (403)
    8. analytics returns 404 for nonexistent assignment
"""

import json

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    Criterion,
    CriteriaDescription,
    Group_Members,
    Review,
    Rubric,
    User,
)
from api.models.db import db as _db


# ── Helpers ──────────────────────────────────────────────────────────────────

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
    """Log in via the cookie-based auth endpoint."""
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _seed_assignment_with_reviews(teacher, num_reviews=1, grade=4, score_max=5):
    """
    Create a full assignment chain:
        teacher → course → assignment → rubric → criteria description
        → group → group members → reviews with criterion scores.

    Returns (assignment, list_of_reviews).
    """
    course = Course(teacherID=teacher.id, name="Analytics Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Analytics Assignment", rubric_text="Rubric")
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

    # Create a group so completion rate can be calculated
    group = CourseGroup(name="Group A", assignmentID=assignment.id)
    _db.session.add(group)
    _db.session.commit()

    reviews = []
    for i in range(num_reviews):
        reviewer = _create_user(f"Reviewer{i}", f"reviewer{i}@test.com")
        reviewee = _create_user(f"Reviewee{i}", f"reviewee{i}@test.com")

        # Add both to group so they count as total_students
        _db.session.add(Group_Members(userID=reviewer.id, groupID=group.id, assignmentID=assignment.id))
        _db.session.add(Group_Members(userID=reviewee.id, groupID=group.id, assignmentID=assignment.id))
        _db.session.commit()

        review = Review(
            assignmentID=assignment.id,
            reviewerID=reviewer.id,
            revieweeID=reviewee.id,
        )
        _db.session.add(review)
        _db.session.commit()

        # Use grade parameter (can be a list for varying scores)
        g = grade[i] if isinstance(grade, list) else grade
        criterion = Criterion(
            reviewID=review.id,
            criterionRowID=crit_desc.id,
            grade=g,
            comments=f"Comment {i}",
        )
        _db.session.add(criterion)
        _db.session.commit()

        reviews.append(review)

    return assignment, reviews


def _seed_empty_assignment(teacher):
    """Create an assignment with no reviews and no group members."""
    course = Course(teacherID=teacher.id, name="Empty Course")
    _db.session.add(course)
    _db.session.commit()

    assignment = Assignment(courseID=course.id, name="Empty Assignment", rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()

    return assignment


# ── Test 1: analytics returns correct structure ──────────────────────────────


def test_analytics_returns_correct_structure(test_client, db):
    """
    GIVEN an authenticated teacher and a seeded assignment with reviews
    WHEN  GET /teacher/assignments/<id>/analytics
    THEN  200 and response contains completion_pct, criteria, and outliers
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _ = _seed_assignment_with_reviews(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/analytics")

    assert resp.status_code == 200
    data = resp.json
    assert "completion_pct" in data
    assert "criteria" in data
    assert "outliers" in data
    assert "assignment_name" in data
    assert "total_students" in data
    assert "submitted" in data


# ── Test 2: analytics empty assignment ───────────────────────────────────────


def test_analytics_empty_assignment(test_client, db):
    """
    GIVEN an assignment with no reviews
    WHEN  GET /teacher/assignments/<id>/analytics
    THEN  200 with completion_pct = 0 and empty arrays
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment = _seed_empty_assignment(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/analytics")

    assert resp.status_code == 200
    assert resp.json["completion_pct"] == 0
    assert resp.json["criteria"] == []
    assert resp.json["outliers"] == []


# ── Test 3: analytics forbidden for student ──────────────────────────────────


def test_analytics_forbidden_for_student(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  GET /teacher/assignments/<id>/analytics
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _ = _seed_assignment_with_reviews(teacher)

    _create_user("Student", "student@test.com", role="student")
    _login(test_client, "student@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/analytics")

    assert resp.status_code == 403


# ── Test 4: CSV export has header row ────────────────────────────────────────


def test_csv_export_has_header_row(test_client, db):
    """
    GIVEN an authenticated teacher and a seeded assignment
    WHEN  GET /teacher/assignments/<id>/export
    THEN  200 with text/csv content type and correct header row
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _ = _seed_assignment_with_reviews(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/export")

    assert resp.status_code == 200
    assert "text/csv" in resp.content_type
    lines = resp.data.decode().splitlines()
    assert lines[0].startswith("review_id")
    # Should have header + at least one data row
    assert len(lines) >= 2


# ── Test 5: completion rate calculation ──────────────────────────────────────


def test_analytics_completion_rate(test_client, db):
    """
    GIVEN 1 reviewer out of 2 group members submitted a review
    WHEN  GET /teacher/assignments/<id>/analytics
    THEN  completion_pct reflects submitted/total correctly
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _ = _seed_assignment_with_reviews(teacher, num_reviews=1)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/analytics")

    assert resp.status_code == 200
    data = resp.json
    # 1 reviewer submitted out of 2 group members (reviewer + reviewee)
    assert data["submitted"] == 1
    assert data["total_students"] == 2
    assert data["completion_pct"] == 50.0


# ── Test 6: outlier detection ────────────────────────────────────────────────


def test_analytics_outlier_detection(test_client, db):
    """
    GIVEN reviews with scores [5,5,5,5,5,5,5,0] (0 is >2σ from mean)
    WHEN  GET /teacher/assignments/<id>/analytics
    THEN  the outlier review is flagged
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    grades = [5, 5, 5, 5, 5, 5, 5, 0]
    assignment, reviews = _seed_assignment_with_reviews(
        teacher, num_reviews=8, grade=grades
    )
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/analytics")

    assert resp.status_code == 200
    outliers = resp.json["outliers"]
    assert len(outliers) >= 1
    # The review with grade=0 should be flagged
    outlier_review_ids = {o["review_id"] for o in outliers}
    assert reviews[7].id in outlier_review_ids


# ── Test 7: CSV export forbidden for student ─────────────────────────────────


def test_csv_export_forbidden_for_student(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  GET /teacher/assignments/<id>/export
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _ = _seed_assignment_with_reviews(teacher)

    _create_user("Student", "student@test.com", role="student")
    _login(test_client, "student@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/export")

    assert resp.status_code == 403


# ── Test 8: analytics returns 404 for nonexistent assignment ─────────────────


def test_analytics_returns_404_for_missing_assignment(test_client, db):
    """
    GIVEN an authenticated teacher
    WHEN  GET /teacher/assignments/99999/analytics
    THEN  404 Not Found
    """
    _create_user("Teacher", "teacher@test.com", role="teacher")
    _login(test_client, "teacher@test.com")

    resp = test_client.get("/teacher/assignments/99999/analytics")

    assert resp.status_code == 404

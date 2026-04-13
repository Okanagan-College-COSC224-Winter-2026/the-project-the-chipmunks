"""
Tests for Task 3 — Teacher Review Dashboard
US13: GET /teacher/assignments/<id>/reviews
US14: GET /teacher/assignments/<id>/reviews/<rev_id>
      POST /teacher/reviews/<rev_id>/conclusion

Test cases from the sprint plan:
    1.  list_reviews returns a list (200)
    2.  list_reviews forbidden for student callers (403)
    3.  get_review_detail contains 'criteria' key (200)
    4.  create_conclusion returns 200 with the saved note
    5.  update_conclusion upserts (second POST updates, does not duplicate)
    + Additional edge-case tests
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
    User_Course,
)
from api.models.conclusion_model import Conclusion
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


def _seed_review(teacher, rubric_score_max=5):
    """
    Create: teacher → course → assignment → rubric → criterion description
                    → student reviewer + reviewee → review + criterion score.
    Returns (assignment, review).
    """
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
        rubricID=rubric.id,
        question="Quality of work",
        scoreMax=rubric_score_max,
        hasScore=True,
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    reviewer = _create_user("Reviewer", "reviewer@test.com")
    reviewee = _create_user("Reviewee", "reviewee@test.com")

    review = Review(
        assignmentID=assignment.id,
        reviewerID=reviewer.id,
        revieweeID=reviewee.id,
    )
    _db.session.add(review)
    _db.session.commit()

    criterion = Criterion(
        reviewID=review.id,
        criterionRowID=crit_desc.id,
        grade=4,
        comments="Great work",
    )
    _db.session.add(criterion)
    _db.session.commit()

    return assignment, review


# ── Test 1: list_reviews returns a list ──────────────────────────────────────


def test_list_reviews_returns_list(test_client, db):
    """
    GIVEN an authenticated teacher and a seeded review
    WHEN  GET /teacher/assignments/<id>/reviews
    THEN  200 and response is a JSON list
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/reviews")

    assert resp.status_code == 200
    assert isinstance(resp.json, list)


# ── Test 2: list_reviews forbidden for students ───────────────────────────────


def test_list_reviews_forbidden_for_student(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  GET /teacher/assignments/<id>/reviews
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, _review = _seed_review(teacher)

    _create_user("Student", "student@test.com", role="student")
    _login(test_client, "student@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/reviews")

    assert resp.status_code == 403


# ── Test 3: get_review_detail has criteria ────────────────────────────────────


def test_get_review_detail_has_criteria(test_client, db):
    """
    GIVEN an authenticated teacher and a seeded review
    WHEN  GET /teacher/assignments/<id>/reviews/<review_id>
    THEN  200 and response contains a 'criteria' list
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews/{review.id}"
    )

    assert resp.status_code == 200
    assert "criteria" in resp.json
    assert isinstance(resp.json["criteria"], list)


# ── Test 4: create_conclusion ─────────────────────────────────────────────────


def test_create_conclusion(test_client, db):
    """
    GIVEN an authenticated teacher and a seeded review
    WHEN  POST /teacher/reviews/<id>/conclusion with a note
    THEN  200 and response contains the saved note
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    _assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({"note": "Good effort overall."}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 200
    assert resp.json["note"] == "Good effort overall."


# ── Test 5: update_conclusion upserts ────────────────────────────────────────


def test_update_conclusion_upserts(test_client, db):
    """
    GIVEN a teacher has already posted a conclusion
    WHEN  they POST again to the same review
    THEN  200 and the note is updated (not duplicated)
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    _assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    # First POST — creates the conclusion
    test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({"note": "First note"}),
        headers={"Content-Type": "application/json"},
    )

    # Second POST — updates it
    resp = test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({"note": "Updated note"}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 200
    assert resp.json["note"] == "Updated note"

    # Confirm only one conclusion row exists in the DB
    count = Conclusion.query.filter_by(reviewID=review.id).count()
    assert count == 1


# ── Additional edge-case tests ────────────────────────────────────────────────


def test_empty_note_returns_400(test_client, db):
    """
    GIVEN an authenticated teacher
    WHEN  POST /teacher/reviews/<id>/conclusion with an empty note
    THEN  400 Bad Request
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    _assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({"note": "   "}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "error" in resp.json


def test_missing_note_field_returns_400(test_client, db):
    """
    GIVEN an authenticated teacher
    WHEN  POST /teacher/reviews/<id>/conclusion with no 'note' key
    THEN  400 Bad Request
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    _assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400


def test_conclusion_endpoint_forbidden_for_student(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  POST /teacher/reviews/<id>/conclusion
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    _assignment, review = _seed_review(teacher)

    _create_user("Student", "student@test.com", role="student")
    _login(test_client, "student@test.com")

    resp = test_client.post(
        f"/teacher/reviews/{review.id}/conclusion",
        data=json.dumps({"note": "Should not save"}),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 403


def test_detail_endpoint_forbidden_for_student(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  GET /teacher/assignments/<id>/reviews/<review_id>
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review = _seed_review(teacher)

    _create_user("Student", "student@test.com", role="student")
    _login(test_client, "student@test.com")

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews/{review.id}"
    )

    assert resp.status_code == 403


def test_list_reviews_sort_by_score(test_client, db):
    """
    GIVEN two reviews with different scores
    WHEN  GET /teacher/assignments/<id>/reviews?sort=score
    THEN  200 and the higher-scoring review appears first
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review_low = _seed_review(teacher)  # grade=4
    _login(test_client, "teacher@test.com")

    # Add a second review with a higher grade
    reviewer2 = _create_user("Reviewer2", "reviewer2@test.com")
    reviewee2 = _create_user("Reviewee2", "reviewee2@test.com")
    review_high = Review(
        assignmentID=assignment.id,
        reviewerID=reviewer2.id,
        revieweeID=reviewee2.id,
    )
    _db.session.add(review_high)
    _db.session.commit()

    # Reuse the same CriteriaDescription from the seeded rubric
    crit_desc = CriteriaDescription.query.filter_by(
        rubricID=Rubric.query.filter_by(assignmentID=assignment.id).first().id
    ).first()
    crit_high = Criterion(
        reviewID=review_high.id,
        criterionRowID=crit_desc.id,
        grade=5,
        comments="Outstanding",
    )
    _db.session.add(crit_high)
    _db.session.commit()

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews?sort=score"
    )

    assert resp.status_code == 200
    scores = [r["total_score"] for r in resp.json]
    assert scores == sorted(scores, reverse=True)


def test_list_reviews_group_filter(test_client, db):
    """
    GIVEN two reviews where only one reviewee is in a specific group
    WHEN  GET /teacher/assignments/<id>/reviews?group_id=<id>
    THEN  200 and only the review for the group member is returned
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    # Create a group and add only review's reviewee to it
    group = CourseGroup(name="Group A", assignmentID=assignment.id)
    _db.session.add(group)
    _db.session.commit()

    membership = Group_Members(
        userID=review.revieweeID,
        groupID=group.id,
        assignmentID=assignment.id,
    )
    _db.session.add(membership)
    _db.session.commit()

    # Add a second review whose reviewee is NOT in the group
    outsider = _create_user("Outsider", "outsider@test.com")
    reviewer2 = _create_user("Reviewer2", "rev2@test.com")
    review_out = Review(
        assignmentID=assignment.id,
        reviewerID=reviewer2.id,
        revieweeID=outsider.id,
    )
    _db.session.add(review_out)
    _db.session.commit()

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews?group_id={group.id}"
    )

    assert resp.status_code == 200
    returned_ids = {r["review_id"] for r in resp.json}
    assert review.id in returned_ids
    assert review_out.id not in returned_ids


def test_detail_shows_conclusion_when_present(test_client, db):
    """
    GIVEN a review that already has a conclusion
    WHEN  GET /teacher/assignments/<id>/reviews/<review_id>
    THEN  200 and 'conclusion' is not null
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    # Seed a conclusion directly
    conclusion = Conclusion(reviewID=review.id, teacherID=teacher.id, note="Pre-existing note")
    Conclusion.create(conclusion)

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews/{review.id}"
    )

    assert resp.status_code == 200
    assert resp.json["conclusion"] is not None
    assert resp.json["conclusion"]["note"] == "Pre-existing note"


def test_detail_conclusion_null_when_absent(test_client, db):
    """
    GIVEN a review with no conclusion
    WHEN  GET /teacher/assignments/<id>/reviews/<review_id>
    THEN  200 and 'conclusion' is null
    """
    teacher = _create_user("Teacher", "teacher@test.com", role="teacher")
    assignment, review = _seed_review(teacher)
    _login(test_client, "teacher@test.com")

    resp = test_client.get(
        f"/teacher/assignments/{assignment.id}/reviews/{review.id}"
    )

    assert resp.status_code == 200
    assert resp.json["conclusion"] is None


def test_unauthenticated_list_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN  GET /teacher/assignments/1/reviews
    THEN  401 Unauthorized
    """
    resp = test_client.get("/teacher/assignments/1/reviews")
    assert resp.status_code == 401


def test_admin_can_access_teacher_endpoints(test_client, db):
    """
    GIVEN an authenticated admin (admins have teacher-level access)
    WHEN  GET /teacher/assignments/<id>/reviews
    THEN  200 (admins pass @jwt_teacher_required)
    """
    admin = _create_user("Admin", "admin@test.com", role="admin")
    assignment, _review = _seed_review(admin)
    _login(test_client, "admin@test.com")

    resp = test_client.get(f"/teacher/assignments/{assignment.id}/reviews")
    assert resp.status_code == 200

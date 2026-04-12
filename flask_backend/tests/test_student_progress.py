"""
Tests for US5 — Instructor Student Progress Dashboard

Endpoint:
    GET /teacher/classes/<course_id>/progress

Test cases:
    1. Teacher receives 200 with correct student and assignment data
    2. Student user receives 403
    3. Non-existent course_id returns 404
    4. Student with no groups shows in_group=False for all assignments
    5. Review counts and avg_score are accurate after seeding reviews
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
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _enroll(user, course):
    uc = User_Course(userID=user.id, courseID=course.id)
    _db.session.add(uc)
    _db.session.commit()
    return uc


def _create_course(teacher, name="Progress Course"):
    course = Course(teacherID=teacher.id, name=name)
    _db.session.add(course)
    _db.session.commit()
    return course


def _create_assignment(course, name="Assignment 1"):
    assignment = Assignment(courseID=course.id, name=name, rubric_text="")
    _db.session.add(assignment)
    _db.session.commit()
    return assignment


def _add_to_group(student, assignment):
    """Put student into a group for the given assignment."""
    group = CourseGroup(assignmentID=assignment.id, name="Group A")
    _db.session.add(group)
    _db.session.commit()
    gm = Group_Members(userID=student.id, groupID=group.id, assignmentID=assignment.id)
    _db.session.add(gm)
    _db.session.commit()
    return group


def _create_review(reviewer, reviewee, assignment, grade=4):
    """Create a review with one criterion score."""
    review = Review(
        assignmentID=assignment.id,
        reviewerID=reviewer.id,
        revieweeID=reviewee.id,
    )
    _db.session.add(review)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    cd = CriteriaDescription(
        rubricID=rubric.id,
        question="Q1",
        scoreMax=5,
    )
    _db.session.add(cd)
    _db.session.commit()

    criterion = Criterion(
        reviewID=review.id,
        criterionRowID=cd.id,
        grade=grade,
        comments="",
    )
    _db.session.add(criterion)
    _db.session.commit()
    return review


# ── Test 1: Teacher receives 200 with correct structure ───────────────────────


def test_progress_teacher_gets_200(test_client, db):
    """
    GIVEN an authenticated teacher, a course with enrolled students and assignments
    WHEN  GET /teacher/classes/<course_id>/progress
    THEN  200 with course_id, course_name, assignments[], and students[]
    """
    teacher = _create_user("Teacher", "teacher_prog@test.com", role="teacher")
    student = _create_user("Alice", "alice_prog@test.com", role="student")
    course = _create_course(teacher)
    assignment = _create_assignment(course)
    _enroll(student, course)

    _login(test_client, "teacher_prog@test.com")
    resp = test_client.get(f"/teacher/classes/{course.id}/progress")

    assert resp.status_code == 200
    data = resp.json
    assert data["course_id"] == course.id
    assert data["course_name"] == course.name
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["id"] == assignment.id
    assert len(data["students"]) == 1
    assert data["students"][0]["email"] == student.email
    assert str(assignment.id) in data["students"][0]["per_assignment"]


# ── Test 2: Student receives 403 ──────────────────────────────────────────────


def test_progress_student_gets_403(test_client, db):
    """
    GIVEN an authenticated student
    WHEN  GET /teacher/classes/<course_id>/progress
    THEN  403 Forbidden
    """
    teacher = _create_user("Teacher", "teacher_403@test.com", role="teacher")
    student = _create_user("Bob", "bob_403@test.com", role="student")
    course = _create_course(teacher)

    _login(test_client, "bob_403@test.com")
    resp = test_client.get(f"/teacher/classes/{course.id}/progress")

    assert resp.status_code == 403


# ── Test 3: Non-existent course returns 404 ───────────────────────────────────


def test_progress_nonexistent_course_returns_404(test_client, db):
    """
    GIVEN an authenticated teacher
    WHEN  GET /teacher/classes/99999/progress for a course that does not exist
    THEN  404 Not Found
    """
    _create_user("Teacher", "teacher_404@test.com", role="teacher")
    _login(test_client, "teacher_404@test.com")

    resp = test_client.get("/teacher/classes/99999/progress")

    assert resp.status_code == 404


# ── Test 4: Student with no groups shows in_group=False ──────────────────────


def test_progress_no_group_shows_false(test_client, db):
    """
    GIVEN a student enrolled in a course but assigned to no group
    WHEN  GET /teacher/classes/<course_id>/progress
    THEN  in_group=False for all assignments
    """
    teacher = _create_user("Teacher", "teacher_ng@test.com", role="teacher")
    student = _create_user("Carol", "carol_ng@test.com", role="student")
    course = _create_course(teacher)
    assignment = _create_assignment(course)
    _enroll(student, course)
    # deliberately do NOT add student to a group

    _login(test_client, "teacher_ng@test.com")
    resp = test_client.get(f"/teacher/classes/{course.id}/progress")

    assert resp.status_code == 200
    student_row = resp.json["students"][0]
    cell = student_row["per_assignment"][str(assignment.id)]
    assert cell["in_group"] is False


# ── Test 5: Review counts and avg_score are accurate ─────────────────────────


def test_progress_review_counts_and_avg_score(test_client, db):
    """
    GIVEN two students, one gives a review to the other with grade=4
    WHEN  GET /teacher/classes/<course_id>/progress
    THEN  reviewer shows reviews_given=1, reviewee shows reviews_received=1 and avg_score=4.0
    """
    teacher = _create_user("Teacher", "teacher_rv@test.com", role="teacher")
    reviewer = _create_user("Dave", "dave_rv@test.com", role="student")
    reviewee = _create_user("Eve", "eve_rv@test.com", role="student")
    course = _create_course(teacher)
    assignment = _create_assignment(course)
    _enroll(reviewer, course)
    _enroll(reviewee, course)
    _create_review(reviewer, reviewee, assignment, grade=4)

    _login(test_client, "teacher_rv@test.com")
    resp = test_client.get(f"/teacher/classes/{course.id}/progress")

    assert resp.status_code == 200
    students = {s["email"]: s for s in resp.json["students"]}

    reviewer_cell = students["dave_rv@test.com"]["per_assignment"][str(assignment.id)]
    reviewee_cell = students["eve_rv@test.com"]["per_assignment"][str(assignment.id)]

    assert reviewer_cell["reviews_given"] == 1
    assert reviewer_cell["reviews_received"] == 0

    assert reviewee_cell["reviews_received"] == 1
    assert reviewee_cell["reviews_given"] == 0
    assert reviewee_cell["avg_score"] == 4.0

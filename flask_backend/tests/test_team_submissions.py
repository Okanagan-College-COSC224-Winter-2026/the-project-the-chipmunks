"""
Tests for the team submissions endpoints (US22).
  GET /student/assignments/<assignment_id>/team-submissions
  GET /student/review-file/<file_id>/download
"""

import json
import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

from api.models import Assignment, Course, Group_Members, Review, ReviewFile, ConclusionFile, User, User_Course
from api.models.course_group_model import CourseGroup
from api.models.db import db as _db


# ============================================================
# HELPERS
# ============================================================


def login_as(test_client, email, password="password"):
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def make_user(name, email, role="student"):
    user = User(name=name, email=email, hash_pass=generate_password_hash("password"), role=role)
    _db.session.add(user)
    _db.session.commit()
    return user


def make_course_and_assignment(teacher):
    course = Course(teacherID=teacher.id, name="Test Course")
    _db.session.add(course)
    _db.session.commit()
    assignment = Assignment(courseID=course.id, name="Assignment 1", rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()
    return course, assignment


def put_in_group(user_id, assignment_id, group=None):
    if group is None:
        group = CourseGroup(name="Group A", assignmentID=assignment_id)
        _db.session.add(group)
        _db.session.commit()
    member = Group_Members(userID=user_id, groupID=group.id, assignmentID=assignment_id)
    _db.session.add(member)
    _db.session.commit()
    return group


def make_review_file(reviewer, assignment_id, filename="report.pdf"):
    review = Review(assignmentID=assignment_id, reviewerID=reviewer.id, revieweeID=reviewer.id)
    _db.session.add(review)
    _db.session.commit()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(b"hello world")
    tmp.flush()
    tmp.close()

    rf = ReviewFile(
        reviewID=review.id,
        filename=filename,
        file_path=tmp.name,
        uploaderID=reviewer.id,
    )
    _db.session.add(rf)
    _db.session.commit()
    return rf, review, tmp.name


# ============================================================
# TESTS — team-submissions list
# ============================================================


def test_returns_group_members_and_files(test_client, db):
    """
    GIVEN a student in a group with one teammate who has a review file
    WHEN GET /student/assignments/<id>/team-submissions
    THEN returns 200 with the teammate's file info (caller excluded)
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    course, assignment = make_course_and_assignment(teacher)

    student = make_user("Student", "student@example.com")
    teammate = make_user("Teammate", "teammate@example.com")

    group = put_in_group(student.id, assignment.id)
    put_in_group(teammate.id, assignment.id, group)

    rf, _, tmp = make_review_file(teammate, assignment.id)

    try:
        login_as(test_client, "student@example.com")
        resp = test_client.get(f"/student/assignments/{assignment.id}/team-submissions")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["assignment_id"] == assignment.id
        assert len(data["group_members"]) == 1
        member = data["group_members"][0]
        assert member["member_id"] == teammate.id
        assert len(member["review_files"]) == 1
        assert member["review_files"][0]["file_id"] == rf.id
        assert member["review_files"][0]["filename"] == "report.pdf"
    finally:
        os.unlink(tmp)


def test_caller_excluded_from_members(test_client, db):
    """
    GIVEN a student in a group
    WHEN GET team-submissions
    THEN the caller does not appear in group_members
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)

    student = make_user("Student", "student@example.com")
    put_in_group(student.id, assignment.id)

    login_as(test_client, "student@example.com")
    resp = test_client.get(f"/student/assignments/{assignment.id}/team-submissions")

    assert resp.status_code == 200
    member_ids = [m["member_id"] for m in resp.get_json()["group_members"]]
    assert student.id not in member_ids


def test_returns_403_when_not_in_group(test_client, db):
    """
    GIVEN a student not in any group for the assignment
    WHEN GET team-submissions
    THEN returns 403
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)
    make_user("Student", "student@example.com")

    login_as(test_client, "student@example.com")
    resp = test_client.get(f"/student/assignments/{assignment.id}/team-submissions")

    assert resp.status_code == 403


def test_returns_404_for_nonexistent_assignment(test_client, db):
    """
    GIVEN a logged-in student
    WHEN GET team-submissions for an assignment that doesn't exist
    THEN returns 404
    """
    make_user("Student", "student@example.com")
    login_as(test_client, "student@example.com")

    resp = test_client.get("/student/assignments/99999/team-submissions")
    assert resp.status_code == 404


def test_conclusion_files_included(test_client, db):
    """
    GIVEN a conclusion file for an assignment
    WHEN GET team-submissions
    THEN conclusion files appear in each member's entry
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)

    student = make_user("Student", "student@example.com")
    teammate = make_user("Teammate", "teammate@example.com")
    group = put_in_group(student.id, assignment.id)
    put_in_group(teammate.id, assignment.id, group)

    cf = ConclusionFile(
        assignmentID=assignment.id,
        filename="conclusion.pdf",
        file_path="/tmp/conclusion.pdf",
        teacherID=teacher.id,
    )
    _db.session.add(cf)
    _db.session.commit()

    login_as(test_client, "student@example.com")
    resp = test_client.get(f"/student/assignments/{assignment.id}/team-submissions")

    assert resp.status_code == 200
    member = resp.get_json()["group_members"][0]
    assert len(member["conclusion_files"]) == 1
    assert member["conclusion_files"][0]["file_id"] == cf.id


def test_no_cross_group_file_leakage(test_client, db):
    """
    GIVEN two groups for the same assignment
    WHEN student from group A calls team-submissions
    THEN only group A members appear
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)

    student_a = make_user("StudentA", "studenta@example.com")
    teammate_a = make_user("TeammateA", "teammatea@example.com")
    student_b = make_user("StudentB", "studentb@example.com")

    group_a = put_in_group(student_a.id, assignment.id)
    put_in_group(teammate_a.id, assignment.id, group_a)
    put_in_group(student_b.id, assignment.id)

    login_as(test_client, "studenta@example.com")
    resp = test_client.get(f"/student/assignments/{assignment.id}/team-submissions")

    assert resp.status_code == 200
    member_ids = [m["member_id"] for m in resp.get_json()["group_members"]]
    assert student_b.id not in member_ids
    assert teammate_a.id in member_ids


# ============================================================
# TESTS — file download
# ============================================================


def test_download_file_same_group(test_client, db):
    """
    GIVEN a student in the same group as the file owner
    WHEN GET /student/review-file/<id>/download
    THEN returns 200 and streams the file
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)

    student = make_user("Student", "student@example.com")
    teammate = make_user("Teammate", "teammate@example.com")
    group = put_in_group(student.id, assignment.id)
    put_in_group(teammate.id, assignment.id, group)

    rf, _, tmp = make_review_file(teammate, assignment.id)

    login_as(test_client, "student@example.com")
    resp = test_client.get(f"/student/review-file/{rf.id}/download")
    assert resp.status_code == 200
    assert resp.data == b"hello world"


def test_download_file_cross_group_returns_403(test_client, db):
    """
    GIVEN a student in a different group than the file owner
    WHEN GET /student/review-file/<id>/download
    THEN returns 403
    """
    teacher = make_user("Teacher", "teacher@example.com", role="teacher")
    _, assignment = make_course_and_assignment(teacher)

    student = make_user("Student", "student@example.com")
    other = make_user("Other", "other@example.com")

    put_in_group(student.id, assignment.id)
    put_in_group(other.id, assignment.id)

    rf, _, tmp = make_review_file(other, assignment.id)

    try:
        login_as(test_client, "student@example.com")
        resp = test_client.get(f"/student/review-file/{rf.id}/download")
        assert resp.status_code == 403
    finally:
        os.unlink(tmp)


def test_download_nonexistent_file_returns_404(test_client, db):
    """
    GIVEN a logged-in student
    WHEN GET /student/review-file/99999/download
    THEN returns 404
    """
    make_user("Student", "student@example.com")
    login_as(test_client, "student@example.com")

    resp = test_client.get("/student/review-file/99999/download")
    assert resp.status_code == 404

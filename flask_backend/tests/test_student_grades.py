"""
Tests for the student grades endpoint (GET /student/grades).
Covers US20 — Student Course Grade on Course Card.

Test cases follow the AAA (Arrange-Act-Assert) pattern.
"""

import json

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    User,
    Course,
    Assignment,
    Review,
    Criterion,
    User_Course,
)
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription
from api.models.db import db as _db


# ============================================================
# HELPER FIXTURES
# ============================================================


@pytest.fixture
def setup_teacher(db):
    """Create a teacher user and a course."""
    teacher = User(
        name="Teacher One",
        email="teacher@example.com",
        hash_pass=generate_password_hash("password"),
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()

    course = Course(teacherID=teacher.id, name="Software Engineering Fall 2025")
    _db.session.add(course)
    _db.session.commit()

    return teacher, course


@pytest.fixture
def setup_student(db):
    """Create a student user."""
    student = User(
        name="Student One",
        email="student@example.com",
        hash_pass=generate_password_hash("password"),
        role="student",
    )
    _db.session.add(student)
    _db.session.commit()
    return student


@pytest.fixture
def setup_reviewer(db):
    """Create a reviewer (peer) user."""
    reviewer = User(
        name="Reviewer One",
        email="reviewer@example.com",
        hash_pass=generate_password_hash("password"),
        role="student",
    )
    _db.session.add(reviewer)
    _db.session.commit()
    return reviewer


def login_as(test_client, email, password="password"):
    """Helper to log in a user via the auth endpoint."""
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def create_assignment_with_rubric(course_id, name="Assignment 1", score_max=5):
    """
    Create an assignment with a rubric and criteria description.
    Returns (assignment, rubric, criteria_description).
    """
    assignment = Assignment(courseID=course_id, name=name, rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    criteria_desc = CriteriaDescription(
        rubricID=rubric.id,
        question="Quality of work",
        scoreMax=score_max,
        hasScore=True,
    )
    _db.session.add(criteria_desc)
    _db.session.commit()

    return assignment, rubric, criteria_desc


def create_review_with_scores(assignment_id, reviewer_id, reviewee_id, criteria_desc_id, grades):
    """
    Create a review with criterion scores.
    grades is a list of integer scores — one Criterion per grade value.
    Returns the review object.
    """
    review = Review(
        assignmentID=assignment_id,
        reviewerID=reviewer_id,
        revieweeID=reviewee_id,
    )
    _db.session.add(review)
    _db.session.commit()

    for grade in grades:
        criterion = Criterion(
            reviewID=review.id,
            criterionRowID=criteria_desc_id,
            grade=grade,
            comments="Test comment",
        )
        _db.session.add(criterion)

    _db.session.commit()
    return review


# ============================================================
# TEST CASES
# ============================================================


def test_get_grades_with_reviews(test_client, db, setup_teacher, setup_student, setup_reviewer):
    """
    GIVEN a student enrolled in a course with completed peer reviews
    WHEN GET /student/grades is called
    THEN return 200 with grade data and has_grades=true
    """
    # Arrange
    teacher, course = setup_teacher
    student = setup_student
    reviewer = setup_reviewer

    User_Course.add(student.id, course.id)

    assignment, rubric, criteria_desc = create_assignment_with_rubric(course.id, score_max=5)
    create_review_with_scores(
        assignment.id, reviewer.id, student.id, criteria_desc.id, [4, 5]
    )

    login_as(test_client, "student@example.com")

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["student_id"] == student.id
    assert len(data["courses"]) == 1

    course_data = data["courses"][0]
    assert course_data["course_id"] == course.id
    assert course_data["course_name"] == "Software Engineering Fall 2025"
    assert course_data["has_grades"] is True
    assert course_data["grade"] is not None
    assert course_data["max_score"] == 5
    assert course_data["graded_assignments"] == 1
    assert course_data["total_assignments"] == 1


def test_get_grades_no_reviews(test_client, db, setup_teacher, setup_student):
    """
    GIVEN a student enrolled in a course with no peer reviews
    WHEN GET /student/grades is called
    THEN return 200 with has_grades=false and grade=null
    """
    # Arrange
    teacher, course = setup_teacher
    student = setup_student

    User_Course.add(student.id, course.id)

    # Create an assignment but no reviews
    create_assignment_with_rubric(course.id)

    login_as(test_client, "student@example.com")

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["courses"]) == 1

    course_data = data["courses"][0]
    assert course_data["has_grades"] is False
    assert course_data["grade"] is None
    assert course_data["max_score"] is None
    assert course_data["graded_assignments"] == 0
    assert course_data["total_assignments"] == 1


def test_get_grades_multiple_courses(test_client, db, setup_student, setup_reviewer):
    """
    GIVEN a student enrolled in 2 courses (one graded, one not)
    WHEN GET /student/grades is called
    THEN return 200 with correct per-course data
    """
    # Arrange
    student = setup_student
    reviewer = setup_reviewer

    teacher = User(
        name="Teacher Two",
        email="teacher2@example.com",
        hash_pass=generate_password_hash("password"),
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()

    # Course 1: has reviews
    course1 = Course(teacherID=teacher.id, name="Course With Grades")
    _db.session.add(course1)
    _db.session.commit()
    User_Course.add(student.id, course1.id)

    assignment1, rubric1, criteria_desc1 = create_assignment_with_rubric(
        course1.id, name="Graded Assignment", score_max=5
    )
    create_review_with_scores(
        assignment1.id, reviewer.id, student.id, criteria_desc1.id, [4, 5, 3]
    )

    # Course 2: no reviews
    course2 = Course(teacherID=teacher.id, name="Course Without Grades")
    _db.session.add(course2)
    _db.session.commit()
    User_Course.add(student.id, course2.id)

    create_assignment_with_rubric(course2.id, name="Ungraded Assignment")

    login_as(test_client, "student@example.com")

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["courses"]) == 2

    graded = next(c for c in data["courses"] if c["course_name"] == "Course With Grades")
    ungraded = next(c for c in data["courses"] if c["course_name"] == "Course Without Grades")

    assert graded["has_grades"] is True
    assert graded["grade"] is not None
    assert graded["graded_assignments"] == 1

    assert ungraded["has_grades"] is False
    assert ungraded["grade"] is None
    assert ungraded["graded_assignments"] == 0


def test_get_grades_unauthenticated(test_client, db):
    """
    GIVEN no user is logged in
    WHEN GET /student/grades is called
    THEN return 401
    """
    # Arrange — no login

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 401


def test_get_grades_no_courses(test_client, db, setup_student):
    """
    GIVEN a student not enrolled in any courses
    WHEN GET /student/grades is called
    THEN return 200 with empty courses array
    """
    # Arrange
    student = setup_student
    login_as(test_client, "student@example.com")

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["student_id"] == student.id
    assert data["courses"] == []


def test_grade_calculation_accuracy(test_client, db, setup_teacher, setup_student, setup_reviewer):
    """
    GIVEN a student with known criterion scores (4, 5, 3)
    WHEN GET /student/grades is called
    THEN the average should be 4.0
    """
    # Arrange
    teacher, course = setup_teacher
    student = setup_student
    reviewer = setup_reviewer

    User_Course.add(student.id, course.id)

    assignment, rubric, criteria_desc = create_assignment_with_rubric(course.id, score_max=5)
    create_review_with_scores(
        assignment.id, reviewer.id, student.id, criteria_desc.id, [4, 5, 3]
    )

    login_as(test_client, "student@example.com")

    # Act
    response = test_client.get("/student/grades")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    course_data = data["courses"][0]

    # (4 + 5 + 3) / 3 = 4.0
    assert course_data["grade"] == 4.0
    assert course_data["has_grades"] is True
    assert course_data["max_score"] == 5


def test_grades_update_with_new_review(
    test_client, db, setup_teacher, setup_student, setup_reviewer
):
    """
    GIVEN a student with an existing grade
    WHEN a new review is submitted and grades are fetched again
    THEN the grade should reflect the new score
    """
    # Arrange
    teacher, course = setup_teacher
    student = setup_student
    reviewer = setup_reviewer

    User_Course.add(student.id, course.id)

    assignment, rubric, criteria_desc = create_assignment_with_rubric(course.id, score_max=5)

    # First review with score of 4
    create_review_with_scores(
        assignment.id, reviewer.id, student.id, criteria_desc.id, [4]
    )

    login_as(test_client, "student@example.com")

    # Act — first fetch
    response1 = test_client.get("/student/grades")
    assert response1.status_code == 200
    grade_before = response1.get_json()["courses"][0]["grade"]

    # Add a second reviewer and review with score of 2
    reviewer2 = User(
        name="Reviewer Two",
        email="reviewer2@example.com",
        hash_pass=generate_password_hash("password"),
        role="student",
    )
    _db.session.add(reviewer2)
    _db.session.commit()

    create_review_with_scores(
        assignment.id, reviewer2.id, student.id, criteria_desc.id, [2]
    )

    # Act — second fetch
    response2 = test_client.get("/student/grades")

    # Assert
    assert response2.status_code == 200
    grade_after = response2.get_json()["courses"][0]["grade"]

    # First grade: 4/1 = 4.0
    assert grade_before == 4.0
    # After adding score of 2: (4 + 2) / 2 = 3.0
    assert grade_after == 3.0

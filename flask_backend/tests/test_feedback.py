"""
Test suite for the Student Feedback Viewing endpoint (US12).
Tests GET /student/assignments/<assignment_id>/feedback

Dev 6 — Poojitha
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models.db import db as _db
from api.models.user_model import User
from api.models.course_model import Course
from api.models.user_course_model import User_Course
from api.models.assignment_model import Assignment
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription
from api.models.review_model import Review
from api.models.criterion_model import Criterion


def login_user(test_client, email, password):
    """Helper to log in a user and get the JWT cookie set."""
    return test_client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def seed_feedback_data(db_session):
    """
    Seed the database with a complete feedback scenario.
    """
    reviewee = User(
        name="Reviewee Student",
        email="reviewee@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    reviewer1 = User(
        name="Reviewer One",
        email="reviewer1@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    reviewer2 = User(
        name="Reviewer Two",
        email="reviewer2@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    no_reviews_student = User(
        name="No Reviews Student",
        email="noreviews@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    wrong_course_student = User(
        name="Wrong Course Student",
        email="wrongcourse@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    teacher = User(
        name="Teacher",
        email="teacher@test.com",
        hash_pass=generate_password_hash("Password123!"),
        role="teacher",
    )

    db_session.add_all([reviewee, reviewer1, reviewer2, no_reviews_student, wrong_course_student, teacher])
    db_session.commit()

    course1 = Course(name="COSC 224", teacherID=teacher.id)
    course2 = Course(name="COSC 304", teacherID=teacher.id)
    db_session.add_all([course1, course2])
    db_session.commit()

    db_session.add(User_Course(userID=reviewee.id, courseID=course1.id))
    db_session.add(User_Course(userID=reviewer1.id, courseID=course1.id))
    db_session.add(User_Course(userID=reviewer2.id, courseID=course1.id))
    db_session.add(User_Course(userID=no_reviews_student.id, courseID=course1.id))
    db_session.add(User_Course(userID=wrong_course_student.id, courseID=course2.id))
    db_session.commit()

    assignment1 = Assignment(courseID=course1.id, name="Peer Review Assignment 1", rubric_text=None)
    assignment2 = Assignment(courseID=course2.id, name="Other Course Assignment", rubric_text=None)
    db_session.add_all([assignment1, assignment2])
    db_session.commit()

    rubric = Rubric(assignmentID=assignment1.id, canComment=True)
    db_session.add(rubric)
    db_session.commit()

    crit_desc1 = CriteriaDescription(rubricID=rubric.id, question="Communication", scoreMax=5, hasScore=True)
    crit_desc2 = CriteriaDescription(rubricID=rubric.id, question="Contribution", scoreMax=5, hasScore=True)
    db_session.add_all([crit_desc1, crit_desc2])
    db_session.commit()

    review1 = Review(assignmentID=assignment1.id, reviewerID=reviewer1.id, revieweeID=reviewee.id)
    review2 = Review(assignmentID=assignment1.id, reviewerID=reviewer2.id, revieweeID=reviewee.id)
    db_session.add_all([review1, review2])
    db_session.commit()

    db_session.add(Criterion(reviewID=review1.id, criterionRowID=crit_desc1.id, grade=4, comments="Good communicator"))
    db_session.add(Criterion(reviewID=review1.id, criterionRowID=crit_desc2.id, grade=3, comments="Could contribute more"))
    db_session.add(Criterion(reviewID=review2.id, criterionRowID=crit_desc1.id, grade=5, comments="Excellent communication"))
    db_session.add(Criterion(reviewID=review2.id, criterionRowID=crit_desc2.id, grade=4, comments=""))
    db_session.commit()

    return {
        "reviewee": reviewee,
        "reviewer1": reviewer1,
        "reviewer2": reviewer2,
        "no_reviews_student": no_reviews_student,
        "wrong_course_student": wrong_course_student,
        "assignment1": assignment1,
        "assignment2": assignment2,
        "crit_desc1": crit_desc1,
        "crit_desc2": crit_desc2,
    }


def test_get_feedback_success(test_client, db):
    data = seed_feedback_data(db.session)
    login_user(test_client, "reviewee@test.com", "Password123!")
    response = test_client.get(f"/student/assignments/{data['assignment1'].id}/feedback")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["assignment_name"] == "Peer Review Assignment 1"
    assert json_data["total_reviews"] == 2
    assert len(json_data["criteria_feedback"]) == 2
    assert "overall_avg" in json_data
    assert json_data["overall_avg"] > 0


def test_get_feedback_no_reviews(test_client, db):
    data = seed_feedback_data(db.session)
    login_user(test_client, "noreviews@test.com", "Password123!")
    response = test_client.get(f"/student/assignments/{data['assignment1'].id}/feedback")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["total_reviews"] == 0
    assert json_data["criteria_feedback"] == []


def test_get_feedback_unauthenticated(test_client, db):
    response = test_client.get("/student/assignments/1/feedback")
    assert response.status_code == 401


def test_get_feedback_assignment_not_found(test_client, db):
    data = seed_feedback_data(db.session)
    login_user(test_client, "reviewee@test.com", "Password123!")
    response = test_client.get("/student/assignments/99999/feedback")
    assert response.status_code == 404


def test_feedback_anonymity(test_client, db):
    data = seed_feedback_data(db.session)
    login_user(test_client, "reviewee@test.com", "Password123!")
    response = test_client.get(f"/student/assignments/{data['assignment1'].id}/feedback")
    assert response.status_code == 200
    json_str = response.get_data(as_text=True)
    assert "reviewer1@test.com" not in json_str
    assert "reviewer2@test.com" not in json_str
    assert "Reviewer One" not in json_str
    assert "Reviewer Two" not in json_str
    assert "reviewerID" not in json_str


def test_feedback_score_aggregation(test_client, db):
    data = seed_feedback_data(db.session)
    login_user(test_client, "reviewee@test.com", "Password123!")
    response = test_client.get(f"/student/assignments/{data['assignment1'].id}/feedback")
    assert response.status_code == 200
    json_data = response.get_json()
    criteria = {cf["question"]: cf for cf in json_data["criteria_feedback"]}
    assert criteria["Communication"]["avg_score"] == 4.5
    assert criteria["Communication"]["max_score"] == 5
    assert criteria["Contribution"]["avg_score"] == 3.5
    assert criteria["Contribution"]["max_score"] == 5
    assert "Good communicator" in criteria["Communication"]["comments"]
    assert "Excellent communication" in criteria["Communication"]["comments"]
    assert "Could contribute more" in criteria["Contribution"]["comments"]
    assert "" not in criteria["Contribution"]["comments"]
    assert json_data["overall_avg"] == 4.0

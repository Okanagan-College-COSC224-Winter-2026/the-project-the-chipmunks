"""
Tests for the PDF export endpoint.
1. Teacher gets 200 with application/pdf
2. Student gets 403
"""
import pytest
from werkzeug.security import generate_password_hash
from api.models import User, Course, Assignment
from api.models.db import db as _db

@pytest.fixture
def teacher_user(test_client):
    """Create a teacher and log them in."""
    user = User(
        name="PDF Teacher",
        email="pdf_teacher@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="teacher",
    )
    _db.session.add(user)
    _db.session.commit()
    test_client.post(
        "/auth/login",
        json={"email": "pdf_teacher@example.com", "password": "Password1!"},
    )
    return user

@pytest.fixture
def student_user(test_client):
    """Create a student and log them in."""
    user = User(
        name="PDF Student",
        email="pdf_student@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )
    _db.session.add(user)
    _db.session.commit()
    test_client.post(
        "/auth/login",
        json={"email": "pdf_student@example.com", "password": "Password1!"},
    )
    return user

@pytest.fixture
def sample_assignment(test_client, teacher_user):
    """Create a sample course and assignment."""
    course = Course(name="PDF Test Course", teacherID=teacher_user.id)
    _db.session.add(course)
    _db.session.commit()
    assignment = Assignment(name="PDF Test Assignment", courseID=course.id, rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()
    return assignment

def test_teacher_can_export_pdf(test_client, teacher_user, sample_assignment):
    """Teacher gets 200 and a PDF file back."""
    resp = test_client.get(
        f"/teacher/assignments/{sample_assignment.id}/export-pdf"
    )
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"

def test_student_cannot_export_pdf(test_client, student_user, sample_assignment):
    """Student gets 403 when trying to export PDF."""
    # Re-login as student since sample_assignment fixture logs in as teacher
    test_client.post(
        "/auth/login",
        json={"email": student_user.email, "password": "Password1!"},
    )
    resp = test_client.get(
        f"/teacher/assignments/{sample_assignment.id}/export-pdf"
    )
    assert resp.status_code == 403
"""
Tests for Feature B — File Attachments on Reviews & Conclusions
Tests for review file upload/download/list and teacher conclusion upload/list.

Test cases (sprint plan):
    1. Student uploads file with review
    2. Invalid file type rejected
    3. File size limit enforced
    4. Download review file works
    5. Teacher uploads conclusion file
    6. Student cannot upload conclusion
    7. Non-authenticated upload rejected
    8. List files for a review
    + Additional edge-case and permission tests
"""

import io
import json

from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    Group_Members,
    Review,
    User,
    User_Course,
)
from api.models.criteria_description_model import CriteriaDescription
from api.models.criterion_model import Criterion
from api.models.db import db as _db
from api.models.rubric_model import Rubric


# ── Helpers ──────────────────────────────────────────────────────────────────


def _login(test_client, email, password="password"):
    """Log in a user via the auth endpoint (sets JWT cookie)."""
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _create_user(name, email, role="student", password="password"):
    """Create a user directly in the DB and return the model instance."""
    user = User(
        name=name,
        email=email,
        hash_pass=generate_password_hash(password),
        role=role,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _create_course(teacher_id, name="Test Course"):
    """Create a course and return it."""
    course = Course(teacherID=teacher_id, name=name)
    _db.session.add(course)
    _db.session.commit()
    return course


def _create_assignment_with_rubric(course_id, name="Assignment 1"):
    """Create an assignment with a rubric + one criteria description."""
    assignment = Assignment(courseID=course_id, name=name, rubric_text="Rubric")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    crit_desc = CriteriaDescription(
        rubricID=rubric.id,
        question="Quality of work",
        scoreMax=5,
        hasScore=True,
    )
    _db.session.add(crit_desc)
    _db.session.commit()

    return assignment, rubric, crit_desc


def _submit_review(test_client, assignment_id, reviewee_id, crit_desc_id):
    """Submit a peer review via the API and return the review_id."""
    resp = test_client.post(
        "/api/reviews/submit",
        data=json.dumps({
            "assignment_id": assignment_id,
            "reviewee_id": reviewee_id,
            "criteria": [
                {
                    "criteria_description_id": crit_desc_id,
                    "grade": 4,
                    "comments": "Good work!",
                }
            ],
        }),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 201, f"Review submission failed: {resp.json}"
    return resp.json["review_id"]


def _setup_review_scenario(test_client):
    """
    Full setup: teacher + course + assignment + 2 students + submitted review.
    Returns (teacher, reviewer, reviewee, assignment, review_id, crit_desc).
    """
    teacher = _create_user("Teacher", "teacher@example.com", role="teacher")
    reviewer = _create_user("Reviewer", "reviewer@example.com", role="student")
    reviewee = _create_user("Reviewee", "reviewee@example.com", role="student")

    course = _create_course(teacher.id)
    User_Course.add(reviewer.id, course.id)
    User_Course.add(reviewee.id, course.id)

    assignment, rubric, crit_desc = _create_assignment_with_rubric(course.id)

    # Log in as reviewer and submit a review
    _login(test_client, "reviewer@example.com")
    review_id = _submit_review(
        test_client, assignment.id, reviewee.id, crit_desc.id
    )

    return teacher, reviewer, reviewee, assignment, review_id, crit_desc


def _make_file(filename="evidence.pdf", size_bytes=1024, content_prefix=b"%PDF-"):
    """Return a (BytesIO, filename) tuple mimicking a file upload."""
    padding_size = max(0, size_bytes - len(content_prefix))
    data = content_prefix + b"0" * padding_size
    return (io.BytesIO(data), filename)


def _upload_review_file(test_client, review_id, file_tuple=None, mime="application/pdf"):
    """Upload a file to a review. Returns the response."""
    if file_tuple is None:
        file_tuple = _make_file()
    stream, filename = file_tuple
    return test_client.post(
        f"/review/{review_id}/upload",
        data={"file": (stream, filename, mime)},
        content_type="multipart/form-data",
    )


def _upload_conclusion_file(test_client, assignment_id, file_tuple=None, mime="application/pdf"):
    """Upload a conclusion file to an assignment. Returns the response."""
    if file_tuple is None:
        file_tuple = _make_file("summary.pdf")
    stream, filename = file_tuple
    return test_client.post(
        f"/assignment/{assignment_id}/conclusion/upload",
        data={"file": (stream, filename, mime)},
        content_type="multipart/form-data",
    )


# ── Test 1: Student uploads file with review ─────────────────────────────────


def test_student_uploads_file_with_review(test_client, db):
    """
    GIVEN a student who submitted a peer review
    WHEN they upload a valid PDF to POST /review/<id>/upload
    THEN the server responds 201 with success and file metadata
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    # reviewer is already logged in from _setup_review_scenario
    resp = _upload_review_file(test_client, review_id)

    assert resp.status_code == 201
    body = resp.json
    assert body["message"] == "File uploaded successfully"
    assert body["filename"] == "evidence.pdf"
    assert "file_id" in body
    assert "size" in body


# ── Test 2: Invalid file type rejected ────────────────────────────────────────


def test_invalid_file_type_rejected(test_client, db):
    """
    GIVEN a student who submitted a review
    WHEN they upload a .exe file
    THEN the server responds 400 with invalid file type message
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    stream = io.BytesIO(b"MZ\x90\x00")  # PE header
    resp = test_client.post(
        f"/review/{review_id}/upload",
        data={"file": (stream, "malware.exe", "application/octet-stream")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "Invalid file type" in resp.json["msg"]


# ── Test 3: File size limit enforced ──────────────────────────────────────────


def test_file_size_limit_enforced(test_client, db):
    """
    GIVEN a student who submitted a review
    WHEN they upload a file larger than 10MB
    THEN the server responds 400 with file-too-large message
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    over_10mb = 10 * 1024 * 1024 + 1
    big_file = _make_file("big.pdf", size_bytes=over_10mb)
    resp = _upload_review_file(test_client, review_id, file_tuple=big_file)

    assert resp.status_code == 400
    assert "File too large" in resp.json["msg"]


# ── Test 4: Download review file works ────────────────────────────────────────


def test_download_review_file(test_client, db):
    """
    GIVEN a review with an attached file
    WHEN an authenticated user requests GET /review/file/<file_id>
    THEN the server responds 200 with the file content
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    upload_resp = _upload_review_file(test_client, review_id)
    file_id = upload_resp.json["file_id"]

    resp = test_client.get(f"/review/file/{file_id}")

    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"


# ── Test 5: Teacher uploads conclusion file ───────────────────────────────────


def test_teacher_uploads_conclusion_file(test_client, db):
    """
    GIVEN a teacher who owns a course with an assignment
    WHEN they POST a PDF to /assignment/<id>/conclusion/upload
    THEN the server responds 201 with success
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    # Log in as teacher
    _login(test_client, "teacher@example.com")
    resp = _upload_conclusion_file(test_client, assignment.id)

    assert resp.status_code == 201
    body = resp.json
    assert body["message"] == "File uploaded successfully"
    assert body["filename"] == "summary.pdf"
    assert "file_id" in body


# ── Test 6: Student cannot upload conclusion ──────────────────────────────────


def test_student_cannot_upload_conclusion(test_client, db):
    """
    GIVEN a student (not a teacher)
    WHEN they try to POST to /assignment/<id>/conclusion/upload
    THEN the server responds 403 (insufficient permissions)
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    # reviewer (student) is logged in
    resp = _upload_conclusion_file(test_client, assignment.id)

    assert resp.status_code == 403


# ── Test 7: Non-authenticated upload rejected ─────────────────────────────────


def test_unauthenticated_review_upload_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN POST /review/<id>/upload is called
    THEN the server responds 401
    """
    stream, filename = _make_file()
    resp = test_client.post(
        "/review/1/upload",
        data={"file": (stream, filename, "application/pdf")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 401


# ── Test 8: List files for a review ───────────────────────────────────────────


def test_list_files_for_review(test_client, db):
    """
    GIVEN a review with uploaded files
    WHEN GET /review/<id>/files is called
    THEN the server responds 200 with a list of file metadata
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    # Upload two files
    _upload_review_file(test_client, review_id, _make_file("doc1.pdf"))
    _upload_review_file(test_client, review_id, _make_file("doc2.pdf"))

    resp = test_client.get(f"/review/{review_id}/files")

    assert resp.status_code == 200
    body = resp.json
    assert body["review_id"] == review_id
    assert len(body["files"]) == 2
    filenames = [f["filename"] for f in body["files"]]
    assert "doc1.pdf" in filenames
    assert "doc2.pdf" in filenames


# ── Additional tests ──────────────────────────────────────────────────────────


def test_unauthenticated_conclusion_upload_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN POST /assignment/<id>/conclusion/upload is called
    THEN the server responds 401
    """
    stream, filename = _make_file()
    resp = test_client.post(
        "/assignment/1/conclusion/upload",
        data={"file": (stream, filename, "application/pdf")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 401


def test_unauthenticated_review_file_list_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN GET /review/<id>/files is called
    THEN the server responds 401
    """
    resp = test_client.get("/review/1/files")
    assert resp.status_code == 401


def test_unauthenticated_review_file_download_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN GET /review/file/<file_id> is called
    THEN the server responds 401
    """
    resp = test_client.get("/review/file/1")
    assert resp.status_code == 401


def test_upload_review_file_to_nonexistent_review(test_client, db):
    """
    GIVEN an authenticated student
    WHEN they upload to a non-existent review id
    THEN the server responds 404
    """
    _create_user("Student", "student@example.com", role="student")
    _login(test_client, "student@example.com")

    resp = _upload_review_file(test_client, 99999)
    assert resp.status_code == 404


def test_non_reviewer_cannot_upload_to_review(test_client, db):
    """
    GIVEN a review submitted by reviewer A
    WHEN reviewer B tries to upload a file to that review
    THEN the server responds 403
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    # Create another student and log in as them
    other_student = _create_user("Other", "other@example.com", role="student")
    _login(test_client, "other@example.com")

    resp = _upload_review_file(test_client, review_id)
    assert resp.status_code == 403
    assert "Unauthorized" in resp.json["msg"]


def test_upload_review_file_no_file_field(test_client, db):
    """
    GIVEN a student who submitted a review
    WHEN they POST without a 'file' field
    THEN the server responds 400
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    resp = test_client.post(
        f"/review/{review_id}/upload",
        data={},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "No file provided" in resp.json["msg"]


def test_upload_png_to_review_succeeds(test_client, db):
    """
    GIVEN a student who submitted a review
    WHEN they upload a valid PNG file
    THEN the server responds 201 (PNG is an allowed type)
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    png_file = _make_file("screenshot.png", content_prefix=b"\x89PNG")
    resp = _upload_review_file(test_client, review_id, file_tuple=png_file, mime="image/png")

    assert resp.status_code == 201
    assert resp.json["filename"] == "screenshot.png"


def test_upload_jpg_to_review_succeeds(test_client, db):
    """
    GIVEN a student who submitted a review
    WHEN they upload a valid JPG file
    THEN the server responds 201 (JPG is an allowed type)
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    jpg_file = _make_file("photo.jpg", content_prefix=b"\xff\xd8\xff")
    resp = _upload_review_file(test_client, review_id, file_tuple=jpg_file, mime="image/jpeg")

    assert resp.status_code == 201
    assert resp.json["filename"] == "photo.jpg"


def test_list_conclusion_files(test_client, db):
    """
    GIVEN a teacher who uploaded conclusion files
    WHEN GET /assignment/<id>/conclusion/files is called
    THEN the response contains the list of conclusion files with teacher name
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    _login(test_client, "teacher@example.com")
    _upload_conclusion_file(test_client, assignment.id, _make_file("grades.pdf"))
    _upload_conclusion_file(test_client, assignment.id, _make_file("feedback.pdf"))

    resp = test_client.get(f"/assignment/{assignment.id}/conclusion/files")

    assert resp.status_code == 200
    body = resp.json
    assert body["assignment_id"] == assignment.id
    assert len(body["files"]) == 2
    # Teacher name should be included
    assert body["files"][0]["teacher"] == "Teacher"


def test_non_owner_teacher_cannot_upload_conclusion(test_client, db):
    """
    GIVEN teacher A owns the course, teacher B does not
    WHEN teacher B tries to upload a conclusion file
    THEN the server responds 403
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    other_teacher = _create_user("Other Teacher", "other_teacher@example.com", role="teacher")
    _login(test_client, "other_teacher@example.com")

    resp = _upload_conclusion_file(test_client, assignment.id)
    assert resp.status_code == 403
    assert "Unauthorized" in resp.json["msg"]


def test_conclusion_upload_to_nonexistent_assignment(test_client, db):
    """
    GIVEN a teacher
    WHEN they upload a conclusion to a non-existent assignment
    THEN the server responds 404
    """
    teacher = _create_user("Teacher", "teacher@example.com", role="teacher")
    _login(test_client, "teacher@example.com")

    resp = _upload_conclusion_file(test_client, 99999)
    assert resp.status_code == 404


def test_download_nonexistent_review_file(test_client, db):
    """
    GIVEN an authenticated user
    WHEN they request GET /review/file/<nonexistent_id>
    THEN the server responds 404
    """
    _create_user("Student", "student@example.com", role="student")
    _login(test_client, "student@example.com")

    resp = test_client.get("/review/file/99999")
    assert resp.status_code == 404


def test_list_files_for_review_with_no_files(test_client, db):
    """
    GIVEN a review that has no file attachments
    WHEN GET /review/<id>/files is called
    THEN the response contains an empty files list
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    resp = test_client.get(f"/review/{review_id}/files")

    assert resp.status_code == 200
    assert resp.json["files"] == []


def test_list_files_for_nonexistent_review(test_client, db):
    """
    GIVEN an authenticated user
    WHEN GET /review/99999/files is called
    THEN the server responds 404
    """
    _create_user("Student", "student@example.com", role="student")
    _login(test_client, "student@example.com")

    resp = test_client.get("/review/99999/files")
    assert resp.status_code == 404


def test_download_conclusion_file(test_client, db):
    """
    GIVEN a teacher uploaded a conclusion file
    WHEN GET /assignment/<id>/conclusion/file/<file_id> is called
    THEN the server responds 200 with the file content
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)

    _login(test_client, "teacher@example.com")
    upload_resp = _upload_conclusion_file(test_client, assignment.id, _make_file("grades.pdf"))
    assert upload_resp.status_code == 201
    file_id = upload_resp.json["file_id"]

    resp = test_client.get(f"/assignment/{assignment.id}/conclusion/file/{file_id}")
    assert resp.status_code == 200


def test_download_nonexistent_conclusion_file(test_client, db):
    """
    GIVEN an authenticated user
    WHEN GET /assignment/<id>/conclusion/file/<nonexistent_id> is called
    THEN the server responds 404
    """
    teacher, reviewer, reviewee, assignment, review_id, _ = _setup_review_scenario(test_client)
    _login(test_client, "teacher@example.com")

    resp = test_client.get(f"/assignment/{assignment.id}/conclusion/file/99999")
    assert resp.status_code == 404


def test_unauthenticated_conclusion_download_rejected(test_client, db):
    """
    GIVEN no user is logged in
    WHEN GET /assignment/<id>/conclusion/file/<file_id> is called
    THEN the server responds 401
    """
    resp = test_client.get("/assignment/1/conclusion/file/1")
    assert resp.status_code == 401

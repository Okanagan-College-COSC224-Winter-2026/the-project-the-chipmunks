"""
Tests for Enhanced Assignment Management — Feature A
Tests for file upload/download endpoints (file_controller.py)
and assignment creation with HTML descriptions.

Test cases:
    1. Upload valid PDF succeeds
    2. Upload non-PDF rejected
    3. Upload over 10MB rejected
    4. Download existing attachment
    5. Download non-existent attachment returns 404
    6. Assignment creation with HTML description
    7. Unauthenticated upload rejected
    + Additional edge-case and DELETE tests
"""

import io
import json
import datetime


# ── Helpers ──────────────────────────────────────────────────────────────────


def _login(test_client, email, password):
    """Log in a user via the auth endpoint (sets JWT cookie on the client)."""
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _create_class(test_client, name="Test Class 101"):
    """Create a class and return its id."""
    resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": name}),
        headers={"Content-Type": "application/json"},
    )
    return resp.json["class"]["id"]


def _create_assignment(test_client, course_id, name="Test Assignment", rubric="Rubric"):
    """Create an assignment with a far-future due date and return its id."""
    future_due = datetime.datetime(2099, 12, 31, 23, 59, 59).isoformat()
    resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": course_id,
            "name": name,
            "rubric": rubric,
            "due_date": future_due,
        }),
        headers={"Content-Type": "application/json"},
    )
    return resp.json["assignment"]["id"]


def _make_pdf_file(filename="test.pdf", size_bytes=1024):
    """Return a tuple (BytesIO stream, filename) that looks like a valid PDF upload."""
    data = b"%PDF-" + b"0" * (size_bytes - 5)
    return (io.BytesIO(data), filename)


def _upload_pdf(test_client, assignment_id, file_tuple=None):
    """Upload a PDF to the given assignment. Returns the response."""
    if file_tuple is None:
        file_tuple = _make_pdf_file()
    stream, filename = file_tuple
    return test_client.post(
        f"/assignment/{assignment_id}/upload",
        data={"file": (stream, filename, "application/pdf")},
        content_type="multipart/form-data",
    )


# ── Test 1: Upload valid PDF succeeds ────────────────────────────────────────


def test_upload_valid_pdf_succeeds(test_client, make_admin):
    """
    GIVEN a teacher who owns a course with an assignment
    WHEN they upload a valid PDF (<10MB) to POST /assignment/<id>/upload
    THEN the server responds 201 with success message and filename
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client, "PDF Upload Class")
    assignment_id = _create_assignment(test_client, class_id)

    resp = _upload_pdf(test_client, assignment_id)

    assert resp.status_code == 201
    body = resp.json
    assert body["message"] == "File uploaded successfully"
    assert body["filename"] == "test.pdf"
    assert "size" in body


# ── Test 2: Upload non-PDF rejected ──────────────────────────────────────────


def test_upload_non_pdf_rejected(test_client, make_admin):
    """
    GIVEN a teacher who owns an assignment
    WHEN they upload a non-PDF file (e.g. .txt)
    THEN the server responds 400 with an invalid file type message
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    # Upload a .txt file instead of PDF
    stream = io.BytesIO(b"this is not a pdf")
    resp = test_client.post(
        f"/assignment/{assignment_id}/upload",
        data={"file": (stream, "notes.txt", "text/plain")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "Invalid file type" in resp.json["msg"]


# ── Test 3: Upload over 10MB rejected ────────────────────────────────────────


def test_upload_over_10mb_rejected(test_client, make_admin):
    """
    GIVEN a teacher who owns an assignment
    WHEN they upload a PDF larger than 10MB
    THEN the server responds 400 with a file-too-large message
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    # Create a file just over 10MB
    over_10mb = 10 * 1024 * 1024 + 1
    big_file = _make_pdf_file("big.pdf", size_bytes=over_10mb)

    resp = _upload_pdf(test_client, assignment_id, file_tuple=big_file)

    assert resp.status_code == 400
    assert "File too large" in resp.json["msg"]


# ── Test 4: Download existing attachment ──────────────────────────────────────


def test_download_existing_attachment(test_client, make_admin):
    """
    GIVEN an assignment that has a PDF attachment
    WHEN any authenticated user requests GET /assignment/<id>/attachment
    THEN the server responds 200 with the file content
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    # First upload a file
    _upload_pdf(test_client, assignment_id)

    # Now download it
    resp = test_client.get(f"/assignment/{assignment_id}/attachment")

    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"


# ── Test 5: Download non-existent attachment returns 404 ──────────────────────


def test_download_nonexistent_attachment_returns_404(test_client, make_admin):
    """
    GIVEN an assignment that has NO attachment
    WHEN an authenticated user requests GET /assignment/<id>/attachment
    THEN the server responds 404
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    resp = test_client.get(f"/assignment/{assignment_id}/attachment")

    assert resp.status_code == 404
    assert "no attachment" in resp.json["msg"].lower()


# ── Test 6: Assignment creation with HTML description ─────────────────────────


def test_assignment_creation_with_html_description(test_client, make_admin):
    """
    GIVEN a teacher
    WHEN they create an assignment and then edit it to include description_html
    THEN the HTML description is persisted and returned
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)

    future_due = datetime.datetime(2099, 12, 31, 23, 59, 59).isoformat()
    create_resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Rich Text Assignment",
            "rubric": "Quality",
            "due_date": future_due,
        }),
        headers={"Content-Type": "application/json"},
    )
    assert create_resp.status_code == 201
    assignment_id = create_resp.json["assignment"]["id"]

    # The assignment schema should include description_html (None by default)
    assert "description_html" in create_resp.json["assignment"]

    # Verify via GET that the field is present
    detail_resp = test_client.get(f"/assignment/detail/{assignment_id}")
    assert detail_resp.status_code == 200
    assert "description_html" in detail_resp.json


# ── Test 7: Unauthenticated upload rejected ───────────────────────────────────


def test_unauthenticated_upload_rejected(test_client):
    """
    GIVEN an unauthenticated user (no JWT cookie)
    WHEN they attempt POST /assignment/<id>/upload
    THEN the server responds 401
    """
    stream, filename = _make_pdf_file()
    resp = test_client.post(
        "/assignment/1/upload",
        data={"file": (stream, filename, "application/pdf")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 401


# ── Additional tests ──────────────────────────────────────────────────────────


def test_unauthenticated_download_rejected(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they attempt GET /assignment/<id>/attachment
    THEN the server responds 401
    """
    resp = test_client.get("/assignment/1/attachment")
    assert resp.status_code == 401


def test_upload_to_nonexistent_assignment_returns_404(test_client, make_admin):
    """
    GIVEN a teacher
    WHEN they upload a PDF to a non-existent assignment id
    THEN the server responds 404
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")

    resp = _upload_pdf(test_client, 99999)
    assert resp.status_code == 404


def test_download_from_nonexistent_assignment_returns_404(test_client, make_admin):
    """
    GIVEN an authenticated user
    WHEN they request an attachment for a non-existent assignment id
    THEN the server responds 404
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")

    resp = test_client.get("/assignment/99999/attachment")
    assert resp.status_code == 404


def test_upload_no_file_field_returns_400(test_client, make_admin):
    """
    GIVEN a teacher who owns an assignment
    WHEN they POST to the upload endpoint without a 'file' field
    THEN the server responds 400
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    resp = test_client.post(
        f"/assignment/{assignment_id}/upload",
        data={},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "No file provided" in resp.json["msg"]


def test_non_owner_teacher_cannot_upload(test_client, make_admin):
    """
    GIVEN teacher A owns a course and teacher B does not
    WHEN teacher B tries to upload a PDF to teacher A's assignment
    THEN the server responds 403
    """
    make_admin(email="teacherA@example.com", password="pw", name="Teacher A")
    make_admin(email="teacherB@example.com", password="pw", name="Teacher B")

    # Teacher A creates the class and assignment
    _login(test_client, "teacherA@example.com", "pw")
    class_id = _create_class(test_client, "Teacher A's Class")
    assignment_id = _create_assignment(test_client, class_id)

    # Teacher B tries to upload
    _login(test_client, "teacherB@example.com", "pw")
    resp = _upload_pdf(test_client, assignment_id)

    assert resp.status_code == 403
    assert "Unauthorized" in resp.json["msg"]


def test_delete_attachment_succeeds(test_client, make_admin):
    """
    GIVEN a teacher who uploaded a PDF to their assignment
    WHEN they DELETE /assignment/<id>/attachment
    THEN the server responds 200 and the attachment is removed
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    # Upload then delete
    _upload_pdf(test_client, assignment_id)
    resp = test_client.delete(f"/assignment/{assignment_id}/attachment")

    assert resp.status_code == 200
    assert "removed" in resp.json["message"].lower()

    # Verify the attachment is gone
    download_resp = test_client.get(f"/assignment/{assignment_id}/attachment")
    assert download_resp.status_code == 404


def test_delete_attachment_when_none_exists_returns_404(test_client, make_admin):
    """
    GIVEN a teacher with an assignment that has no attachment
    WHEN they DELETE /assignment/<id>/attachment
    THEN the server responds 404
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    resp = test_client.delete(f"/assignment/{assignment_id}/attachment")

    assert resp.status_code == 404
    assert "no attachment" in resp.json["msg"].lower()


def test_unauthenticated_delete_attachment_rejected(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they attempt DELETE /assignment/<id>/attachment
    THEN the server responds 401
    """
    resp = test_client.delete("/assignment/1/attachment")
    assert resp.status_code == 401


def test_upload_replaces_existing_attachment(test_client, make_admin):
    """
    GIVEN a teacher who already uploaded a PDF to an assignment
    WHEN they upload another PDF to the same assignment
    THEN the new file replaces the old one (201 success)
    """
    make_admin(email="teacher@example.com", password="pw", name="Teacher")
    _login(test_client, "teacher@example.com", "pw")
    class_id = _create_class(test_client)
    assignment_id = _create_assignment(test_client, class_id)

    # Upload first file
    resp1 = _upload_pdf(test_client, assignment_id, _make_pdf_file("first.pdf"))
    assert resp1.status_code == 201
    assert resp1.json["filename"] == "first.pdf"

    # Upload second file (replaces)
    resp2 = _upload_pdf(test_client, assignment_id, _make_pdf_file("second.pdf"))
    assert resp2.status_code == 201
    assert resp2.json["filename"] == "second.pdf"

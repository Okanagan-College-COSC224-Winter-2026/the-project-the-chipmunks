"""
File controller for the peer evaluation app.
Handles PDF file upload and download for assignment attachments.

Endpoints:
    POST /assignment/<id>/upload     — Upload a PDF attachment (teacher only)
    GET  /assignment/<id>/attachment — Download the assignment's PDF attachment
    DELETE /assignment/<id>/attachment — Remove attachment from assignment (teacher only)
"""

import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, User
from .auth_controller import jwt_teacher_required

file_bp = Blueprint("file", __name__, url_prefix="/assignment")

# Maximum allowed upload size: 10MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSION = "pdf"


def _get_upload_dir():
    """Return the absolute path to the uploads directory, creating it if needed."""
    upload_dir = os.path.join(current_app.instance_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _is_pdf(file) -> bool:
    """
    Validate that the uploaded file is a PDF.
    Checks both the filename extension and the MIME type reported by the client.
    Server-side validation only — never trust the client alone.
    """
    filename = file.filename or ""
    extension_ok = filename.lower().endswith(f".{ALLOWED_EXTENSION}")
    mimetype_ok = file.mimetype == "application/pdf"
    return extension_ok and mimetype_ok


def _file_size_bytes(file) -> int:
    """
    Measure the file size in bytes without consuming the stream.
    Seeks to end to measure, then resets to start before saving.
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


# ============================================================
# POST /assignment/<id>/upload
# Upload a PDF attachment to an assignment (teacher only)
# ============================================================

@file_bp.route("/<int:assignment_id>/upload", methods=["POST"])
@jwt_teacher_required
def upload_attachment(assignment_id):
    """
    Upload a PDF file and attach it to an assignment.

    Expects multipart/form-data with a 'file' field containing the PDF.

    Validations:
        1. Assignment must exist
        2. Authenticated user must be the teacher of the assignment's course
        3. Uploaded file must be a PDF (extension + MIME type)
        4. File must be <= 10MB

    Returns:
        201 { "message": str, "filename": str, "size": str }
        400 — missing file, wrong type, or oversized
        403 — authenticated user is not the teacher
        404 — assignment not found
    """
    # ── Resolve assignment ────────────────────────────────────────────────────
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # ── Confirm caller is the teacher of this assignment's course ─────────────
    email = get_jwt_identity()
    teacher = User.get_by_email(email)
    if teacher is None:
        return jsonify({"msg": "User not found"}), 404

    if assignment.course.teacherID != teacher.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this assignment's course"}), 403

    # ── Validate file presence ────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"msg": "No file provided. Include a 'file' field in your multipart/form-data request"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "" or uploaded_file.filename is None:
        return jsonify({"msg": "No file selected"}), 400

    # ── Validate file type (PDF only) ─────────────────────────────────────────
    if not _is_pdf(uploaded_file):
        return jsonify({"msg": "Invalid file type. Only PDF files are accepted"}), 400

    # ── Enforce 10MB size limit ───────────────────────────────────────────────
    file_size = _file_size_bytes(uploaded_file)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return jsonify({"msg": f"File too large ({size_mb:.1f}MB). Maximum allowed size is 10MB"}), 400

    # ── Build a safe filename scoped to this assignment ───────────────────────
    # Format: assignment_<id>_<original_filename>
    # This avoids collisions between assignments and keeps names readable.
    original_filename = uploaded_file.filename
    safe_filename = f"assignment_{assignment_id}_{original_filename}"
    upload_dir = _get_upload_dir()
    save_path = os.path.join(upload_dir, safe_filename)

    # ── Save file to disk ─────────────────────────────────────────────────────
    uploaded_file.save(save_path)

    # ── Persist attachment metadata on the assignment record ──────────────────
    assignment.attachment_filename = original_filename
    assignment.attachment_path = save_path
    assignment.update()

    size_mb = file_size / (1024 * 1024)
    return jsonify({
        "message": "File uploaded successfully",
        "filename": original_filename,
        "size": f"{size_mb:.1f}MB",
    }), 201


# ============================================================
# GET /assignment/<id>/attachment
# Download the PDF attachment for an assignment (any authenticated user)
# ============================================================

@file_bp.route("/<int:assignment_id>/attachment", methods=["GET"])
@jwt_required()
def download_attachment(assignment_id):
    """
    Download the PDF attachment for a given assignment.

    Returns the file as an inline download response.

    Returns:
        200 — file download response
        404 — assignment not found, or no attachment exists
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    if not assignment.attachment_path or not assignment.attachment_filename:
        return jsonify({"msg": "This assignment has no attachment"}), 404

    # Verify the file still exists on disk
    if not os.path.isfile(assignment.attachment_path):
        return jsonify({"msg": "Attachment file not found on server"}), 404

    upload_dir = _get_upload_dir()
    safe_filename = f"assignment_{assignment_id}_{assignment.attachment_filename}"

    return send_from_directory(
        upload_dir,
        safe_filename,
        as_attachment=True,
        download_name=assignment.attachment_filename,
    )


# ============================================================
# DELETE /assignment/<id>/attachment
# Remove the attachment from an assignment (teacher only)
# ============================================================

@file_bp.route("/<int:assignment_id>/attachment", methods=["DELETE"])
@jwt_teacher_required
def delete_attachment(assignment_id):
    """
    Remove the PDF attachment from an assignment and delete the file from disk.

    Returns:
        200 { "message": str }
        403 — authenticated user is not the teacher
        404 — assignment not found, or no attachment exists
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # ── Confirm caller is the teacher of this assignment's course ─────────────
    email = get_jwt_identity()
    teacher = User.get_by_email(email)
    if teacher is None:
        return jsonify({"msg": "User not found"}), 404

    if assignment.course.teacherID != teacher.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this assignment's course"}), 403

    if not assignment.attachment_path or not assignment.attachment_filename:
        return jsonify({"msg": "This assignment has no attachment to remove"}), 404

    # ── Delete file from disk if it still exists ──────────────────────────────
    if os.path.isfile(assignment.attachment_path):
        os.remove(assignment.attachment_path)

    # ── Clear attachment metadata from the assignment record ──────────────────
    assignment.attachment_filename = None
    assignment.attachment_path = None
    assignment.update()

    return jsonify({"message": "Attachment removed successfully"}), 200

"""
Review & Conclusion file controller for the peer evaluation app.
Handles file uploads/downloads for peer review attachments and teacher conclusions.

Endpoints:
    POST   /review/<id>/upload          — Upload file(s) with review (student)
    GET    /review/<id>/files           — List files attached to a review
    GET    /review/file/<file_id>       — Download a specific review file
    POST   /assignment/<id>/conclusion/upload  — Upload conclusion file (teacher)
    GET    /assignment/<id>/conclusion/files   — List conclusion files for assignment
    GET    /assignment/<id>/conclusion/file/<file_id> — Download a specific conclusion file
"""

import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, Review, User
from ..models.review_file_model import ReviewFile
from ..models.conclusion_file_model import ConclusionFile
from .auth_controller import jwt_teacher_required

review_file_bp = Blueprint("review_file", __name__)

# Maximum allowed upload size: 10MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Accepted file types: PDF, PNG, JPG/JPEG, DOCX
ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _get_review_upload_dir():
    """Return the absolute path to the review uploads directory."""
    upload_dir = os.path.join(current_app.instance_path, "uploads", "reviews")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _get_conclusion_upload_dir():
    """Return the absolute path to the conclusion uploads directory."""
    upload_dir = os.path.join(current_app.instance_path, "uploads", "conclusions")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _is_allowed_file(file) -> bool:
    """Validate that the uploaded file has an allowed extension and MIME type."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False
    expected_mime = ALLOWED_EXTENSIONS[ext]
    return file.mimetype == expected_mime


def _file_size_bytes(file) -> int:
    """Measure file size without consuming the stream."""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


# ============================================================
# POST /review/<id>/upload — Upload file with review (student)
# ============================================================

@review_file_bp.route("/review/<int:review_id>/upload", methods=["POST"])
@jwt_required()
def upload_review_file(review_id):
    """Upload a file attachment to an existing review."""
    review = Review.get_by_id(review_id)
    if review is None:
        return jsonify({"msg": "Review not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    # Only the reviewer who submitted the review can attach files
    if review.reviewerID != user.id:
        return jsonify({"msg": "Unauthorized: Only the reviewer can upload files to this review"}), 403

    if "file" not in request.files:
        return jsonify({"msg": "No file provided"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "" or uploaded_file.filename is None:
        return jsonify({"msg": "No file selected"}), 400

    if not _is_allowed_file(uploaded_file):
        return jsonify({"msg": "Invalid file type. Allowed types: PDF, PNG, JPG, DOCX"}), 400

    file_size = _file_size_bytes(uploaded_file)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return jsonify({"msg": f"File too large ({size_mb:.1f}MB). Maximum allowed size is 10MB"}), 400

    original_filename = uploaded_file.filename
    safe_filename = f"review_{review_id}_{original_filename}"
    upload_dir = _get_review_upload_dir()
    save_path = os.path.join(upload_dir, safe_filename)

    uploaded_file.save(save_path)

    review_file = ReviewFile(
        reviewID=review_id,
        filename=original_filename,
        file_path=save_path,
        uploaderID=user.id,
    )
    ReviewFile.create(review_file)

    size_mb = file_size / (1024 * 1024)
    return jsonify({
        "message": "File uploaded successfully",
        "file_id": review_file.id,
        "filename": original_filename,
        "size": f"{size_mb:.1f}MB",
    }), 201


# ============================================================
# GET /review/<id>/files — List files attached to a review
# ============================================================

@review_file_bp.route("/review/<int:review_id>/files", methods=["GET"])
@jwt_required()
def list_review_files(review_id):
    """List all files attached to a review."""
    review = Review.get_by_id(review_id)
    if review is None:
        return jsonify({"msg": "Review not found"}), 404

    files = ReviewFile.get_by_review(review_id)
    return jsonify({
        "review_id": review_id,
        "files": [
            {
                "file_id": f.id,
                "filename": f.filename,
                "uploaded_at": f.uploaded_at.isoformat() + "Z" if f.uploaded_at else None,
                "size": f"{os.path.getsize(f.file_path) / (1024 * 1024):.1f}MB"
                if os.path.isfile(f.file_path) else "0MB",
            }
            for f in files
        ],
    }), 200


# ============================================================
# GET /review/file/<file_id> — Download a specific review file
# ============================================================

@review_file_bp.route("/review/file/<int:file_id>", methods=["GET"])
@jwt_required()
def download_review_file(file_id):
    """Download a specific review file by its ID."""
    review_file = ReviewFile.get_by_id(file_id)
    if review_file is None:
        return jsonify({"msg": "File not found"}), 404

    if not os.path.isfile(review_file.file_path):
        return jsonify({"msg": "File not found on server"}), 404

    directory = os.path.dirname(review_file.file_path)
    basename = os.path.basename(review_file.file_path)

    return send_from_directory(
        directory,
        basename,
        as_attachment=True,
        download_name=review_file.filename,
    )


# ============================================================
# POST /assignment/<id>/conclusion/upload — Teacher uploads conclusion file
# ============================================================

@review_file_bp.route("/assignment/<int:assignment_id>/conclusion/upload", methods=["POST"])
@jwt_teacher_required
def upload_conclusion_file(assignment_id):
    """Upload a conclusion/summary file to an assignment (teacher only)."""
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    teacher = User.get_by_email(email)
    if teacher is None:
        return jsonify({"msg": "User not found"}), 404

    if assignment.course.teacherID != teacher.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this assignment's course"}), 403

    if "file" not in request.files:
        return jsonify({"msg": "No file provided"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "" or uploaded_file.filename is None:
        return jsonify({"msg": "No file selected"}), 400

    if not _is_allowed_file(uploaded_file):
        return jsonify({"msg": "Invalid file type. Allowed types: PDF, PNG, JPG, DOCX"}), 400

    file_size = _file_size_bytes(uploaded_file)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return jsonify({"msg": f"File too large ({size_mb:.1f}MB). Maximum allowed size is 10MB"}), 400

    original_filename = uploaded_file.filename
    safe_filename = f"conclusion_{assignment_id}_{original_filename}"
    upload_dir = _get_conclusion_upload_dir()
    save_path = os.path.join(upload_dir, safe_filename)

    uploaded_file.save(save_path)

    conclusion_file = ConclusionFile(
        assignmentID=assignment_id,
        filename=original_filename,
        file_path=save_path,
        teacherID=teacher.id,
    )
    ConclusionFile.create(conclusion_file)

    size_mb = file_size / (1024 * 1024)
    return jsonify({
        "message": "File uploaded successfully",
        "file_id": conclusion_file.id,
        "filename": original_filename,
        "size": f"{size_mb:.1f}MB",
    }), 201


# ============================================================
# GET /assignment/<id>/conclusion/file/<file_id> — Download conclusion file
# ============================================================

@review_file_bp.route("/assignment/<int:assignment_id>/conclusion/file/<int:file_id>", methods=["GET"])
@jwt_required()
def download_conclusion_file(assignment_id, file_id):
    """Download a specific conclusion file by its ID."""
    conclusion_file = ConclusionFile.get_by_id(file_id)
    if conclusion_file is None or conclusion_file.assignmentID != assignment_id:
        return jsonify({"msg": "File not found"}), 404

    if not os.path.isfile(conclusion_file.file_path):
        return jsonify({"msg": "File not found on server"}), 404

    directory = os.path.dirname(conclusion_file.file_path)
    basename = os.path.basename(conclusion_file.file_path)

    return send_from_directory(
        directory,
        basename,
        as_attachment=True,
        download_name=conclusion_file.filename,
    )


# ============================================================
# GET /assignment/<id>/conclusion/files — List conclusion files
# ============================================================

@review_file_bp.route("/assignment/<int:assignment_id>/conclusion/files", methods=["GET"])
@jwt_required()
def list_conclusion_files(assignment_id):
    """List all conclusion files for an assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    files = ConclusionFile.get_by_assignment(assignment_id)
    return jsonify({
        "assignment_id": assignment_id,
        "files": [
            {
                "file_id": f.id,
                "filename": f.filename,
                "uploaded_at": f.uploaded_at.isoformat() + "Z" if f.uploaded_at else None,
                "teacher": f.teacher.name if f.teacher else None,
            }
            for f in files
        ],
    }), 200
"""
Submission controller for the peer evaluation app.
Handles student assignment file submissions (individual or group).

Endpoints:
    POST   /assignment/<id>/submission/upload          — Upload a submission file
    GET    /assignment/<id>/submission/status          — Get submission status for current user
    DELETE /assignment/<id>/submission/<sub_id>        — Delete a submission
    GET    /assignment/<id>/submission/<sub_id>/download — Download a submission file
"""

import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, User, Group_Members
from ..models.submission_model import Submission

submission_bp = Blueprint("submission", __name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
}


def _get_submission_upload_dir():
    upload_dir = os.path.join(current_app.instance_path, "uploads", "submissions")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _is_allowed_file(file) -> bool:
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def _file_size_bytes(file) -> int:
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


# ============================================================
# POST /assignment/<id>/submission/upload
# Upload a submission file (student)
# ============================================================

@submission_bp.route("/assignment/<int:assignment_id>/submission/upload", methods=["POST"])
@jwt_required()
def upload_submission(assignment_id):
    """Upload a submission file for an assignment."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    mode = request.form.get("mode", "individual")
    if mode not in ("individual", "group"):
        return jsonify({"msg": "Invalid mode. Must be 'individual' or 'group'"}), 400

    # For group mode, verify the student is in a group for this assignment
    group_id = None
    if mode == "group":
        membership = Group_Members.query.filter_by(
            userID=user.id, assignmentID=assignment_id
        ).first()
        if membership is None:
            return jsonify({"msg": "You are not in a group for this assignment"}), 403
        group_id = membership.groupID

    if "file" not in request.files:
        return jsonify({"msg": "No file provided"}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"msg": "No file selected"}), 400

    if not _is_allowed_file(uploaded_file):
        return jsonify({"msg": "Invalid file type. Allowed: PDF, PNG, JPG, DOCX, ZIP"}), 400

    file_size = _file_size_bytes(uploaded_file)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return jsonify({"msg": f"File too large ({size_mb:.1f}MB). Maximum is 10MB"}), 400

    original_filename = uploaded_file.filename
    safe_filename = f"sub_{assignment_id}_{user.id}_{original_filename}"
    upload_dir = _get_submission_upload_dir()
    save_path = os.path.join(upload_dir, safe_filename)
    uploaded_file.save(save_path)

    submission = Submission(
        assignmentID=assignment_id,
        studentID=user.id,
        filename=original_filename,
        file_path=save_path,
        submission_mode=mode,
        group_id=group_id,
    )
    Submission.create(submission)

    return jsonify({
        "message": "Submission uploaded successfully",
        "submission": _serialize(submission, user),
    }), 201


# ============================================================
# GET /assignment/<id>/submission/status
# Get current user's submission status
# ============================================================

@submission_bp.route("/assignment/<int:assignment_id>/submission/status", methods=["GET"])
@jwt_required()
def get_submission_status(assignment_id):
    """Return the current user's individual and group submissions for an assignment."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # Individual submissions by this student
    individual = Submission.get_by_student_assignment(user.id, assignment_id)

    # Group submissions (if in a group)
    group_submissions = []
    group_id = None
    membership = Group_Members.query.filter_by(
        userID=user.id, assignmentID=assignment_id
    ).first()
    if membership:
        group_id = membership.groupID
        group_submissions = Submission.get_by_group_assignment(group_id, assignment_id)

    return jsonify({
        "assignment_id": assignment_id,
        "group_id": group_id,
        "individual_submissions": [_serialize(s, user) for s in individual],
        "group_submissions": [_serialize(s, user) for s in group_submissions],
    }), 200


# ============================================================
# DELETE /assignment/<id>/submission/<sub_id>
# Delete a submission (owner only)
# ============================================================

@submission_bp.route("/assignment/<int:assignment_id>/submission/<int:submission_id>",
                     methods=["DELETE"])
@jwt_required()
def delete_submission(assignment_id, submission_id):
    """Delete a submission. Only the uploader can delete their own file."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    submission = Submission.get_by_id(submission_id)
    if submission is None or submission.assignmentID != assignment_id:
        return jsonify({"msg": "Submission not found"}), 404

    if submission.studentID != user.id:
        return jsonify({"msg": "Unauthorized: You can only delete your own submissions"}), 403

    # Remove file from disk
    if os.path.isfile(submission.file_path):
        os.remove(submission.file_path)

    submission.delete()
    return jsonify({"message": "Submission deleted"}), 200


# ============================================================
# GET /assignment/<id>/submission/<sub_id>/download
# Download a submission file
# ============================================================

@submission_bp.route("/assignment/<int:assignment_id>/submission/<int:submission_id>/download",
                     methods=["GET"])
@jwt_required()
def download_submission(assignment_id, submission_id):
    """Download a submission file. Accessible by the uploader and group members."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    submission = Submission.get_by_id(submission_id)
    if submission is None or submission.assignmentID != assignment_id:
        return jsonify({"msg": "Submission not found"}), 404

    # Access check: must be the uploader, or a group member (for group submissions)
    if submission.studentID != user.id:
        if submission.submission_mode == "group" and submission.group_id:
            membership = Group_Members.query.filter_by(
                userID=user.id, assignmentID=assignment_id
            ).first()
            if membership is None or membership.groupID != submission.group_id:
                return jsonify({"msg": "Unauthorized"}), 403
        else:
            return jsonify({"msg": "Unauthorized"}), 403

    if not os.path.isfile(submission.file_path):
        return jsonify({"msg": "File not found on server"}), 404

    directory = os.path.dirname(submission.file_path)
    basename = os.path.basename(submission.file_path)

    return send_from_directory(
        directory,
        basename,
        as_attachment=True,
        download_name=submission.filename,
    )


def _serialize(submission, current_user):
    """Serialize a Submission to a dict for JSON responses."""
    return {
        "id": submission.id,
        "filename": submission.filename,
        "submission_mode": submission.submission_mode,
        "uploaded_at": submission.uploaded_at.isoformat() if submission.uploaded_at else None,
        "uploaded_by": submission.student.name if submission.student else None,
        "is_mine": submission.studentID == current_user.id,
    }

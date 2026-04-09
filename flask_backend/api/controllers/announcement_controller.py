"""
Announcement controller for the peer evaluation app.

Routes:
  GET    /announcement/course/<course_id>/announcements  – list announcements for a course
  POST   /announcement/course/<course_id>/announcements  – create an announcement (teacher/admin)
  DELETE /announcement/announcements/<id>                – delete an announcement (teacher/admin)
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models import Course, User
from api.models.announcement_model import Announcement
from api.models.db import db
from .auth_controller import jwt_teacher_required

announcement_bp = Blueprint("announcement", __name__, url_prefix="/announcement")


@announcement_bp.route("/course/<int:course_id>/announcements", methods=["GET"])
@jwt_required()
def list_announcements(course_id):
    """
    GET /announcement/course/<course_id>/announcements
    Returns all announcements for the given course, newest first.
    """
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404

    announcements = (
        Announcement.query
        .filter_by(course_id=course_id)
        .order_by(Announcement.created_at.desc())
        .all()
    )
    return jsonify({"announcements": [a.to_dict() for a in announcements]}), 200


@announcement_bp.route("/course/<int:course_id>/announcements", methods=["POST"])
@jwt_teacher_required
def create_announcement(course_id):
    """
    POST /announcement/course/<course_id>/announcements
    Body: { "title": str, "content": str }
    Creates a new announcement for the course. Teacher/admin only.
    """
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404

    email = get_jwt_identity()
    author = User.get_by_email(email)
    if not author:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title:
        return jsonify({"msg": "Title is required"}), 400
    if not content:
        return jsonify({"msg": "Content is required"}), 400

    announcement = Announcement(
        course_id=course_id,
        author_id=author.id,
        title=title,
        content=content,
    )
    db.session.add(announcement)
    db.session.commit()

    # Notify all enrolled students
    from api.models import User_Course
    from api.services.notification_service import create_notification

    enrollments = User_Course.query.filter_by(courseID=course_id).all()
    for enrollment in enrollments:
        if enrollment.user and enrollment.user.id != author.id:
            create_notification(
                user_id=enrollment.user.id,
                type="announcement",
                title=f"New Announcement: {title}",
                message=f"{author.name} posted an announcement in {course.name}.",
                link=f"/classes/{course_id}/home",
            )

    return jsonify({"announcement": announcement.to_dict()}), 201


@announcement_bp.route("/announcements/<int:announcement_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_announcement(announcement_id):
    """
    DELETE /announcement/announcements/<announcement_id>
    Deletes an announcement. Teacher/admin only.
    """
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({"msg": "Announcement not found"}), 404

    db.session.delete(announcement)
    db.session.commit()
    return jsonify({"msg": "Announcement deleted"}), 200

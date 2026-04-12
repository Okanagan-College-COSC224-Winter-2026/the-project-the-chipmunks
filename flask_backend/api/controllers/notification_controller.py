"""
Notification controller for the peer evaluation app.
Provides endpoints for managing user notifications.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models.db import db
from api.models.notification_model import Notification
from api.models.user_model import User
from api.schemas.notification_schema import notifications_schema

notification_bp = Blueprint("notification", __name__, url_prefix="/notification")


@notification_bp.route("/notifications", methods=["GET"])
@jwt_required()
def list_notifications():
    """GET /notification/notifications — paginated, newest first."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    type_filter = request.args.get("type")

    query = Notification.query.filter_by(user_id=user.id)
    if type_filter:
        query = query.filter_by(type=type_filter)
    query = query.order_by(Notification.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "notifications": notifications_schema.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }), 200


@notification_bp.route("/notifications/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    """GET /notification/notifications/unread-count — count of unread notifications."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"unread_count": count}), 200


@notification_bp.route("/notifications/<int:notif_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notif_id):
    """PUT /notification/notifications/<id>/read — mark single notification as read."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    notification = Notification.query.filter_by(id=notif_id, user_id=user.id).first()
    if notification is None:
        return jsonify({"msg": "Notification not found"}), 404

    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read"}), 200


@notification_bp.route("/notifications/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    """PUT /notification/notifications/read-all — mark all unread as read."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    Notification.query.filter_by(user_id=user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify({"message": "All marked as read"}), 200

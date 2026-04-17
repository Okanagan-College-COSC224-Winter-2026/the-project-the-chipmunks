"""
Message controller for the peer evaluation app.
Handles in-group student messaging for a given CourseGroup.

Endpoints:
    GET /message/group/<group_id>       — fetch all messages (group members only)
    POST /message/group/<group_id>      — send a new message
    PUT /message/group/<group_id>/read  — mark others' messages as read

Auth:   JWT cookie — get_jwt_identity() returns email → resolved to user.id
Writes: Message table only. No other tables are touched.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from api.models.db import db
from api.models.group_members_model import Group_Members
from api.models.message_model import Message
from api.models.user_model import User
from api.schemas.message_schema import message_schema, messages_schema

message_bp = Blueprint("message", __name__, url_prefix="/message")


# ── Private helper ────────────────────────────────────────────────────────────

def _user_in_group(user_id: int, group_id: int) -> bool:
    """
    Return True if the user is a member of the given CourseGroup.
    Queries the Group_Members table using the project's actual column names
    (userID / groupID — PascalCase, matching group_members_model.py).
    """
    return (
        Group_Members.query
        .filter_by(userID=user_id, groupID=group_id)
        .first()
    ) is not None


# ============================================================
# GET /message/group/<group_id>
# Fetch all messages for a group (oldest-first)
# ============================================================

@message_bp.route("/group/<int:group_id>", methods=["GET"])
@jwt_required()
def get_messages(group_id):
    """
    Return all messages for a group in chronological order.
    Only members of the group may read its messages.

    Response 200: [ { message fields } ]
    Response 403: caller is not a group member
    Response 404: user not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    if not _user_in_group(user.id, group_id):
        return jsonify({"error": "Not a member of this group"}), 403

    msgs = Message.get_by_group(group_id)
    return jsonify(messages_schema.dump(msgs)), 200


# ============================================================
# POST /message/group/<group_id>
# Send a new message to the group
# ============================================================

@message_bp.route("/group/<int:group_id>", methods=["POST"])
@jwt_required()
def send_message(group_id):
    """
    Create a new message in the group on behalf of the authenticated user.
    Content must be non-empty after stripping whitespace.

    Request body (JSON): { "content": str }

    Response 201: serialised message
    Response 400: empty or missing content
    Response 403: caller is not a group member
    Response 404: user not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    if not _user_in_group(user.id, group_id):
        return jsonify({"error": "Not a member of this group"}), 403

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message content required"}), 400

    msg = Message(groupID=group_id, senderID=user.id, content=content)
    Message.create(msg)

    return jsonify(message_schema.dump(msg)), 201


# ============================================================
# PUT /message/group/<group_id>/read
# Mark all of the other members' messages as read
# ============================================================

@message_bp.route("/group/<int:group_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(group_id):
    """
    Mark all unread messages in this group that were NOT sent by the
    current user as is_read=True.

    Response 200: { "message": "Marked as read" }
    Response 404: user not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    Message.query.filter(
        Message.groupID == group_id,
        Message.senderID != user.id,
        Message.is_read.is_(False),
    ).update({"is_read": True})
    db.session.commit()

    return jsonify({"message": "Marked as read"}), 200
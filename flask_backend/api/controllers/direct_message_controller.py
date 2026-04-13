"""
Direct message controller for the peer evaluation app.
Handles private 1-on-1 messaging between any two users.

Endpoints:
    GET  /message/direct/<other_user_id>  — fetch conversation thread
    POST /message/direct/<other_user_id>  — send a direct message
    PUT  /message/direct/<other_user_id>/read — mark incoming messages as read
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from api.models.db import db
from api.models.direct_message_model import DirectMessage
from api.models.user_model import User

direct_message_bp = Blueprint("direct_message", __name__, url_prefix="/message")


@direct_message_bp.route("/direct/<int:other_user_id>", methods=["GET"])
@jwt_required()
def get_direct_messages(other_user_id):
    """
    GET /message/direct/<other_user_id>
    Returns the full conversation thread between the current user and other_user_id,
    ordered oldest-first.

    Response 200: [ { message fields } ]
    Response 404: current user or other user not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    other = db.session.get(User, other_user_id)
    if other is None:
        return jsonify({"msg": "Recipient not found"}), 404

    messages = DirectMessage.get_conversation(user.id, other_user_id)
    return jsonify([m.to_dict() for m in messages]), 200


@direct_message_bp.route("/direct/<int:other_user_id>", methods=["POST"])
@jwt_required()
def send_direct_message(other_user_id):
    """
    POST /message/direct/<other_user_id>
    Send a private message to another user.

    Request body (JSON): { "content": str }

    Response 201: serialised message
    Response 400: empty or missing content
    Response 404: current user or recipient not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    other = db.session.get(User, other_user_id)
    if other is None:
        return jsonify({"msg": "Recipient not found"}), 404

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message content required"}), 400

    msg = DirectMessage(senderID=user.id, recipientID=other_user_id, content=content)
    db.session.add(msg)
    db.session.commit()

    return jsonify(msg.to_dict()), 201


@direct_message_bp.route("/direct/<int:other_user_id>/read", methods=["PUT"])
@jwt_required()
def mark_direct_read(other_user_id):
    """
    PUT /message/direct/<other_user_id>/read
    Mark all messages from other_user_id to the current user as read.

    Response 200: { "message": "Marked as read" }
    Response 404: current user not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    DirectMessage.mark_read(reader_id=user.id, sender_id=other_user_id)
    return jsonify({"message": "Marked as read"}), 200

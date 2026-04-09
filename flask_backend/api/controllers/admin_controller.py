"""
Admin management endpoints
Only admin users can access these endpoints
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import Schema, fields, validate
from werkzeug.security import generate_password_hash

from ..models import User, UserSchema
from ..models.db import db
from .auth_controller import jwt_admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---- Validation schemas for admin endpoints ----

class AdminUserCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True, validate=validate.OneOf(["student", "teacher", "admin"]))
    must_change_password = fields.Bool(load_default=False)


class AdminUserUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    email = fields.Email()
    role = fields.Str(validate=validate.OneOf(["student", "teacher", "admin"]))
    password = fields.Str(validate=validate.Length(min=6))


# ---- Endpoints ----

@bp.route("/users", methods=["GET"])
@jwt_admin_required
def list_all_users():
    """List all users with pagination, role filter, and search (admin only)"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    role = request.args.get("role", None)
    search = request.args.get("search", None)

    query = User.query

    if role:
        query = query.filter_by(role=role)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.email.ilike(like),
                User.name.ilike(like),
            )
        )

    pagination = query.order_by(User.id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "users": UserSchema(many=True).dump(pagination.items),
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
    }), 200


@bp.route("/users/create", methods=["POST"])
@jwt_admin_required
def create_user():
    """Create a new user with any role (admin only)"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    schema = AdminUserCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"msg": "Validation error", "errors": errors}), 400

    data = schema.load(request.json)

    # Check if user already exists
    existing_user = User.get_by_email(data["email"])
    if existing_user:
        return jsonify({"msg": f"User with email {data['email']} is already registered"}), 409

    # Create new user
    new_user = User(
        name=data["name"],
        hash_pass=generate_password_hash(data["password"]),
        email=data["email"],
        role=data["role"],
        must_change_password=data.get("must_change_password", False),
    )
    User.create_user(new_user)

    return (
        jsonify({
            "msg": f"{data['role'].capitalize()} account created successfully",
            "user": UserSchema().dump(new_user),
        }),
        201,
    )


@bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_admin_required
def update_user(user_id):
    """Update a user's name, email, role, or password (admin only)"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    schema = AdminUserUpdateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"msg": "Validation error", "errors": errors}), 400

    data = schema.load(request.json)

    # Check email uniqueness if changing email
    if "email" in data and data["email"] != user.email:
        existing = User.get_by_email(data["email"])
        if existing:
            return jsonify({"msg": "Email already in use"}), 409

    # Prevent self-demotion from admin
    if "role" in data:
        current_email = get_jwt_identity()
        current_user = User.get_by_email(current_email)
        if current_user and current_user.id == user_id and data["role"] != "admin":
            return jsonify({"msg": "Cannot demote yourself from admin role"}), 400

    for field, value in data.items():
        if field == "password":
            user.hash_pass = generate_password_hash(value)
        else:
            setattr(user, field, value)

    user.update()

    return jsonify({
        "msg": "User updated successfully",
        "user": UserSchema().dump(user),
    }), 200


@bp.route("/users/<int:user_id>/role", methods=["PUT"])
@jwt_admin_required
def update_user_role(user_id):
    """Update a user's role (admin only) — legacy endpoint kept for compatibility"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    new_role = request.json.get("role", None)

    if not new_role:
        return jsonify({"msg": "Role is required"}), 400

    if new_role not in ["student", "teacher", "admin"]:
        return jsonify({"msg": "Invalid role. Must be 'student', 'teacher', or 'admin'"}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    current_email = get_jwt_identity()
    current_user = User.get_by_email(current_email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    if current_user.id == user_id and new_role != "admin":
        return jsonify({"msg": "Cannot demote yourself from admin role"}), 400

    old_role = user.role
    user.role = new_role
    user.update()

    return (
        jsonify({
            "msg": f"User role updated from {old_role} to {new_role}",
            "user": UserSchema().dump(user),
        }),
        200,
    )


@bp.route("/users/<int:user_id>/deactivate", methods=["PATCH"])
@jwt_admin_required
def deactivate_user(user_id):
    """Deactivate a user account (soft-delete) — admin only"""
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    current_email = get_jwt_identity()
    current_user = User.get_by_email(current_email)
    if current_user and current_user.id == user_id:
        return jsonify({"msg": "Cannot deactivate yourself"}), 400

    user.is_active = False
    user.update()

    return jsonify({"msg": "User deactivated"}), 200


@bp.route("/users/<int:user_id>/reactivate", methods=["PATCH"])
@jwt_admin_required
def reactivate_user(user_id):
    """Reactivate a deactivated user account — admin only"""
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.is_active = True
    user.update()

    return jsonify({"msg": "User reactivated"}), 200


@bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    current_email = get_jwt_identity()
    current_user = User.get_by_email(current_email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    if current_user.id == user_id:
        return jsonify({"msg": "Cannot delete your own account"}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.delete()

    return jsonify({"msg": "User deleted successfully"}), 200
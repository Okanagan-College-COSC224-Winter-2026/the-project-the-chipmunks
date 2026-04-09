"""
Group controller for the peer evaluation app.
Provides all group management endpoints used by the Group page.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, CourseGroup, Group_Members, User, User_Course
from .auth_controller import jwt_teacher_required

group_bp = Blueprint("group", __name__)


# ============================================================
# GET /list_stu_groups/<assignment_id>/<student_id>
# Returns the group members in the same group as the given student
# for the given assignment. Used on the Assignment home tab.
# ============================================================
@group_bp.route("/list_stu_groups/<int:assignment_id>/<int:student_id>", methods=["GET"])
@jwt_required()
def list_stu_groups(assignment_id, student_id):
    """Return all group members in the same group as the student.
    If the student has no group, fall back to all other enrolled students
    so they can still submit peer reviews."""
    membership = Group_Members.query.filter_by(
        userID=student_id, assignmentID=assignment_id
    ).first()

    if membership:
        # Student is in a group — return the other group members
        group_id = membership.groupID
        members = Group_Members.query.filter_by(
            groupID=group_id, assignmentID=assignment_id
        ).all()
        return jsonify([
            {"userID": m.userID, "groupID": m.groupID, "assignmentID": m.assignmentID}
            for m in members
            if m.userID != student_id
        ]), 200

    # No group assigned — fall back to all other enrolled students in the course
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify([]), 200

    enrollments = User_Course.query.filter_by(courseID=assignment.courseID).all()
    return jsonify([
        {"userID": e.userID, "groupID": -1, "assignmentID": assignment_id}
        for e in enrollments
        if e.userID != student_id
    ]), 200


# ============================================================
# GET /list_all_groups/<assignment_id>
# Returns all CourseGroups for the given assignment.
# ============================================================
@group_bp.route("/list_all_groups/<int:assignment_id>", methods=["GET"])
@jwt_required()
def list_all_groups(assignment_id):
    """Return all groups for an assignment."""
    groups = CourseGroup.query.filter_by(assignmentID=assignment_id).all()
    return jsonify([
        {"id": g.id, "name": g.name, "assignmentID": g.assignmentID}
        for g in groups
    ]), 200


# ============================================================
# GET /list_ua_groups/<assignment_id>
# Returns all enrolled students NOT assigned to any group
# for the given assignment.
# ============================================================
@group_bp.route("/list_ua_groups/<int:assignment_id>", methods=["GET"])
@jwt_required()
def list_ua_groups(assignment_id):
    """Return all students enrolled in the course who have no group for this assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify([]), 200

    # All students enrolled in the course
    enrollments = User_Course.query.filter_by(courseID=assignment.courseID).all()
    enrolled_ids = {e.userID for e in enrollments}

    # Students already assigned to a group
    assigned = Group_Members.query.filter_by(assignmentID=assignment_id).all()
    assigned_ids = {m.userID for m in assigned}

    unassigned_ids = enrolled_ids - assigned_ids

    return jsonify([
        {"userID": uid, "groupID": -1, "assignmentID": assignment_id}
        for uid in unassigned_ids
    ]), 200


# ============================================================
# GET /list_group_members/<assignment_id>/<group_id>
# Returns all members of a specific group.
# ============================================================
@group_bp.route("/list_group_members/<int:assignment_id>/<int:group_id>", methods=["GET"])
@jwt_required()
def list_group_members(assignment_id, group_id):
    """Return all members of a specific group."""
    members = Group_Members.query.filter_by(
        groupID=group_id, assignmentID=assignment_id
    ).all()
    return jsonify([
        {"userID": m.userID, "groupID": m.groupID, "assignmentID": m.assignmentID}
        for m in members
    ]), 200


# ============================================================
# GET /user_id
# Returns the current logged-in user's ID.
# ============================================================
@group_bp.route("/user_id", methods=["GET"])
@jwt_required()
def get_user_id():
    """Return the current user's ID."""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user.id), 200


# ============================================================
# GET /next_groupid?assignmentID=<id>
# Returns the highest existing group ID for this assignment,
# so the frontend can compute the next one.
# ============================================================
@group_bp.route("/next_groupid", methods=["GET"])
@jwt_required()
def next_group_id():
    """Return the max group ID for an assignment (frontend adds 1 to get next)."""
    assignment_id = request.args.get("assignmentID", type=int)
    if not assignment_id:
        return jsonify(0), 200

    groups = CourseGroup.query.filter_by(assignmentID=assignment_id).all()
    if not groups:
        return jsonify(0), 200

    max_id = max(g.id for g in groups)
    return jsonify(max_id), 200


# ============================================================
# POST /create_group
# Creates a new CourseGroup for the assignment.
# ============================================================
@group_bp.route("/create_group", methods=["POST"])
@jwt_teacher_required
def create_group():
    """Create a new group for an assignment."""
    data = request.get_json() or {}
    assignment_id = data.get("assignmentID")
    name = data.get("name", "New Group")

    if not assignment_id:
        return jsonify({"msg": "assignmentID is required"}), 400

    group = CourseGroup(name=name, assignmentID=assignment_id)
    CourseGroup.create_group(group)

    return jsonify({"id": group.id, "name": group.name, "assignmentID": group.assignmentID}), 201


# ============================================================
# POST /delete_group
# Deletes a CourseGroup and all its memberships.
# ============================================================
@group_bp.route("/delete_group", methods=["POST"])
@jwt_teacher_required
def delete_group():
    """Delete a group by ID."""
    data = request.get_json() or {}
    group_id = data.get("groupID")

    if not group_id:
        return jsonify({"msg": "groupID is required"}), 400

    group = CourseGroup.get_by_id(group_id)
    if not group:
        return jsonify({"msg": "Group not found"}), 404

    group.delete()
    return jsonify({"msg": "Group deleted"}), 200


# ============================================================
# POST /save_groups
# Saves a single student's group assignment.
# Called repeatedly by the frontend for every member.
# ============================================================
@group_bp.route("/save_groups", methods=["POST"])
@jwt_teacher_required
def save_groups():
    """Assign a student to a group (or remove from group if groupID == -1)."""
    data = request.get_json() or {}
    group_id = data.get("groupID")
    user_id = data.get("userID")
    assignment_id = data.get("assignmentID")

    if user_id is None or assignment_id is None:
        return jsonify({"msg": "userID and assignmentID are required"}), 400

    # Remove any existing group membership for this student in this assignment
    existing = Group_Members.query.filter_by(
        userID=user_id, assignmentID=assignment_id
    ).all()
    for m in existing:
        m.delete()

    # If groupID is -1 the student is being moved to unassigned — nothing more to do
    if group_id == -1 or group_id is None:
        return jsonify({"msg": "Student unassigned"}), 200

    # Create the new membership
    Group_Members.create_group_member(
        userID=user_id,
        groupID=group_id,
        assignmentID=assignment_id,
    )

    return jsonify({"msg": "Group saved"}), 200

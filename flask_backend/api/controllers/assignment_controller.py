"""
Assignment controller for the peer evaluation app.

Routes use the /assignment prefix from the blueprint.
Frontend calls: /assignment/create_assignment, /assignment/detail/<id>,
/assignment/edit_assignment/<id>, /assignment/delete_assignment/<id>, /assignment/<class_id>
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models import Assignment, Course, User
from api.models.db import db
from .auth_controller import jwt_teacher_required

bp = Blueprint("assignment", __name__, url_prefix="/assignment")


# ---------------------------------------------------------------------
# GET /assignment/<class_id> — List assignments for a course
# ---------------------------------------------------------------------

@bp.route("/<int:class_id>", methods=["GET"])
@jwt_required()
def get_assignments_by_class(class_id):
    """Return all assignments for a given course."""
    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    assignments = Assignment.get_by_class_id(class_id)
    result = []
    for a in assignments:
        result.append({
            "id": a.id,
            "courseID": a.courseID,
            "name": a.name,
            "rubric": a.rubric_text,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "description_html": a.description_html,
            "attachment_filename": a.attachment_filename,
            "has_attachment": a.attachment_filename is not None,
        })
    return jsonify(result), 200


# ---------------------------------------------------------------------
# GET /assignment/detail/<assignment_id> — Get single assignment
# ---------------------------------------------------------------------

@bp.route("/detail/<int:assignment_id>", methods=["GET"])
@jwt_required()
def get_assignment_detail(assignment_id):
    """Return a single assignment by ID."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    return jsonify({
        "id": assignment.id,
        "courseID": assignment.courseID,
        "name": assignment.name,
        "rubric": assignment.rubric_text,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "description_html": assignment.description_html,
        "attachment_filename": assignment.attachment_filename,
        "has_attachment": assignment.attachment_filename is not None,
    }), 200


# ---------------------------------------------------------------------
# POST /assignment/create_assignment — Create a new assignment
# ---------------------------------------------------------------------

@bp.route("/create_assignment", methods=["POST"])
@jwt_teacher_required
def create_assignment():
    """Create a new assignment for a course. Teacher must own the course."""
    data = request.get_json() or {}

    course_id = data.get("courseID")
    name = data.get("name")

    if not course_id or not name:
        return jsonify({"msg": "courseID and name are required"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    if course.teacherID != user.id:
        return jsonify({"msg": "Forbidden: you are not the teacher of this class"}), 403

    rubric_text = data.get("rubric", "")
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.fromisoformat(data["due_date"])
        except ValueError:
            return jsonify({"msg": "Invalid date format"}), 400

    description_html = data.get("description_html", "")

    assignment = Assignment(
        courseID=course_id,
        name=name,
        rubric_text=rubric_text,
        due_date=due_date,
        description_html=description_html,
    )
    Assignment.create(assignment)

    return jsonify({
        "msg": "Assignment created",
        "assignment": {
            "id": assignment.id,
            "courseID": assignment.courseID,
            "name": assignment.name,
            "rubric": assignment.rubric_text,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "description_html": assignment.description_html,
        }
    }), 201


# ---------------------------------------------------------------------
# PATCH /assignment/edit_assignment/<assignment_id> — Edit assignment
# ---------------------------------------------------------------------

@bp.route("/edit_assignment/<int:assignment_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_assignment(assignment_id):
    """Edit an assignment. Teacher must own the course. Cannot edit past due date."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    if not assignment.can_modify():
        return jsonify({"msg": "Cannot edit: assignment is past due date"}), 403

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course or course.teacherID != user.id:
        return jsonify({"msg": "Forbidden: you are not the teacher of this class"}), 403

    data = request.get_json() or {}

    if "name" in data:
        assignment.name = data["name"]
    if "rubric" in data:
        assignment.rubric_text = data["rubric"]
    if "description_html" in data:
        assignment.description_html = data["description_html"]
    if "due_date" in data:
        try:
            assignment.due_date = datetime.fromisoformat(data["due_date"]) if data["due_date"] else None
        except ValueError:
            return jsonify({"msg": "Invalid date format"}), 400

    assignment.update()

    return jsonify({
        "msg": "Assignment updated",
        "assignment": {
            "id": assignment.id,
            "courseID": assignment.courseID,
            "name": assignment.name,
            "rubric": assignment.rubric_text,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "description_html": assignment.description_html,
        }
    }), 200


# ---------------------------------------------------------------------
# DELETE /assignment/delete_assignment/<assignment_id>
# ---------------------------------------------------------------------

@bp.route("/delete_assignment/<int:assignment_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment(assignment_id):
    """Delete an assignment. Teacher must own the course. Cannot delete past due date."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    if not assignment.can_modify():
        return jsonify({"msg": "Cannot delete: assignment is past due date"}), 403

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course or course.teacherID != user.id:
        return jsonify({"msg": "Forbidden: you are not the teacher of this class"}), 403

    assignment.delete()
    return jsonify({"msg": "Assignment deleted"}), 200


# ---------------------------------------------------------------------
# Rubric endpoints (used by frontend)
# ---------------------------------------------------------------------

@bp.route("/<int:assignment_id>/rubric", methods=["POST"])
@jwt_teacher_required
def create_rubric(assignment_id):
    """Create a rubric for an assignment."""
    from api.models import Rubric
    data = request.get_json() or {}
    can_comment = data.get("canComment", True)

    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    # Remove existing rubric if any
    existing = Rubric.query.filter_by(assignmentID=assignment_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    rubric = Rubric(assignmentID=assignment_id, canComment=can_comment)
    db.session.add(rubric)
    db.session.commit()

    return jsonify({"id": rubric.id}), 201


@bp.route("/rubric/<int:rubric_id>/criteria", methods=["POST"])
@jwt_teacher_required
def create_criteria(rubric_id):
    """Add a criterion to a rubric."""
    from api.models import CriteriaDescription
    data = request.get_json() or {}

    question = data.get("question", "")
    score_max = data.get("scoreMax", 5)
    has_score = data.get("hasScore", True)

    criteria = CriteriaDescription(
        rubricID=rubric_id,
        question=question,
        scoreMax=score_max,
        hasScore=has_score,
    )
    db.session.add(criteria)
    db.session.commit()

    return jsonify({"id": criteria.id}), 201


@bp.route("/criteria", methods=["GET"])
@jwt_required()
def get_criteria():
    """Get criteria for a rubric by rubricID query param."""
    from api.models import CriteriaDescription
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    criteria = CriteriaDescription.query.filter_by(rubricID=int(rubric_id)).all()
    result = []
    for c in criteria:
        result.append({
            "id": c.id,
            "rubricID": c.rubricID,
            "question": c.question,
            "scoreMax": c.scoreMax,
            "hasScore": c.hasScore,
        })
    return jsonify(result), 200


@bp.route("/rubric/by-id", methods=["GET"])
@jwt_required()
def get_rubric_by_id():
    """Get a rubric by rubricID query param."""
    from api.models import Rubric
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    rubric = Rubric.query.get(int(rubric_id))
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    return jsonify({
        "id": rubric.id,
        "assignmentID": rubric.assignmentID,
        "canComment": rubric.canComment,
    }), 200


@bp.route("/<int:assignment_id>/rubric", methods=["GET"])
@jwt_required()
def get_rubric_by_assignment(assignment_id):
    """Get the rubric and criteria for an assignment."""
    from api.models import Rubric, CriteriaDescription

    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    rubric = Rubric.query.filter_by(assignmentID=assignment_id).first()
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    criteria = CriteriaDescription.query.filter_by(rubricID=rubric.id).all()
    return jsonify({
        "rubric_id": rubric.id,
        "assignment_id": assignment_id,
        "criteria": [
            {
                "id": c.id,
                "question": c.question,
                "score_max": c.scoreMax,
                "has_score": c.hasScore,
                "can_comment": rubric.canComment,
            }
            for c in criteria
        ],
    }), 200


@bp.route("/review", methods=["GET"])
@jwt_required()
def get_review():
    """Get review grades by query params."""
    from api.models import Review, Criterion

    assignment_id = request.args.get("assignmentID")
    reviewer_id = request.args.get("reviewerID")
    reviewee_id = request.args.get("revieweeID")

    if not all([assignment_id, reviewer_id, reviewee_id]):
        return jsonify({"msg": "Missing required parameters"}), 400

    review = Review.query.filter_by(
        assignmentID=int(assignment_id),
        reviewerID=int(reviewer_id),
        revieweeID=int(reviewee_id),
    ).first()

    if not review:
        return jsonify({"msg": "Review not found"}), 404

    criteria = Criterion.query.filter_by(reviewID=review.id).all()
    grades = [c.grade for c in criteria]

    return jsonify({"grades": grades}), 200

"""
Rubric Builder controller for the peer evaluation app.
Provides endpoints for building and managing advanced rubrics.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from api.models.db import db
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription
from api.schemas.rubric_builder_schema import rubric_builder_input, rubric_output, rubrics_output

rubric_builder_bp = Blueprint("rubric_builder", __name__, url_prefix="/rubric-builder")


def _serialize_rubric(rubric):
    """Convert a Rubric + its CriteriaDescription rows into the output dict."""
    criteria = (
        CriteriaDescription.query
        .filter_by(rubricID=rubric.id)
        .order_by(CriteriaDescription.position)
        .all()
    )
    return {
        "id": rubric.id,
        "assignment_id": rubric.assignmentID,
        "name": rubric.canComment,  # repurpose — see below
        "is_template": rubric.is_template,
        "template_name": rubric.template_name,
        "criteria": [
            {
                "id": c.id,
                "name": c.question,
                "description": c.description or "",
                "max_score": c.scoreMax,
                "weight": c.weight or 0,
                "position": c.position,
            }
            for c in criteria
        ],
    }


def _rubric_name(rubric):
    """Return the rubric builder 'name'. Stored in template_name for builder rubrics."""
    return rubric.template_name


def _serialize_rubric_full(rubric):
    """Serialize rubric with proper name field."""
    criteria = (
        CriteriaDescription.query
        .filter_by(rubricID=rubric.id)
        .order_by(CriteriaDescription.position)
        .all()
    )
    return {
        "id": rubric.id,
        "assignment_id": rubric.assignmentID,
        "name": rubric.template_name or "",
        "is_template": rubric.is_template,
        "template_name": rubric.template_name,
        "criteria": [
            {
                "id": c.id,
                "name": c.question,
                "description": c.description or "",
                "max_score": c.scoreMax,
                "weight": c.weight or 0,
                "position": c.position,
            }
            for c in criteria
        ],
    }


@rubric_builder_bp.route("/assignment/<int:assignment_id>/rubric", methods=["GET"])
@jwt_required()
def get_rubric(assignment_id):
    """GET /rubric-builder/assignment/<id>/rubric — get rubric for assignment."""
    rubric = Rubric.get_rubric_by_assignment(assignment_id)
    if rubric is None:
        return jsonify({"rubric": None}), 200
    return jsonify({"rubric": _serialize_rubric_full(rubric)}), 200


@rubric_builder_bp.route("/assignment/<int:assignment_id>/rubric", methods=["PUT"])
@jwt_required()
def upsert_rubric(assignment_id):
    """PUT /rubric-builder/assignment/<id>/rubric — create or update rubric."""
    try:
        data = rubric_builder_input.load(request.json)
    except ValidationError as err:
        return jsonify({"msg": err.messages}), 400

    rubric = Rubric.get_rubric_by_assignment(assignment_id)

    if rubric is None:
        rubric = Rubric(assignmentID=assignment_id)
        db.session.add(rubric)
        db.session.flush()

    rubric.template_name = data["name"]
    rubric.is_template = data.get("is_template", False)
    if data.get("template_name") is not None:
        rubric.template_name = data["template_name"]

    # Sync criteria
    incoming_ids = {c["id"] for c in data["criteria"] if c.get("id") is not None}
    existing = CriteriaDescription.query.filter_by(rubricID=rubric.id).all()

    for existing_cd in existing:
        if existing_cd.id not in incoming_ids:
            db.session.delete(existing_cd)

    for c in data["criteria"]:
        if c.get("id") is not None and c["id"] in {e.id for e in existing}:
            cd = CriteriaDescription.get_by_id(c["id"])
            if cd and cd.rubricID == rubric.id:
                cd.question = c["name"]
                cd.description = c.get("description", "")
                cd.scoreMax = c["max_score"]
                cd.weight = c["weight"]
                cd.position = c["position"]
        else:
            cd = CriteriaDescription(
                rubricID=rubric.id,
                question=c["name"],
                scoreMax=c["max_score"],
            )
            cd.description = c.get("description", "")
            cd.weight = c["weight"]
            cd.position = c["position"]
            db.session.add(cd)

    db.session.commit()
    return jsonify({"rubric": _serialize_rubric_full(rubric)}), 200


@rubric_builder_bp.route("/rubric/<int:rubric_id>/reorder", methods=["PUT"])
@jwt_required()
def reorder_criteria(rubric_id):
    """PUT /rubric-builder/rubric/<id>/reorder — reorder criteria."""
    data = request.json or {}
    order = data.get("order", [])

    for index, criterion_id in enumerate(order):
        cd = CriteriaDescription.get_by_id(criterion_id)
        if cd and cd.rubricID == rubric_id:
            cd.position = index

    db.session.commit()
    return jsonify({"message": "Reordered"}), 200


@rubric_builder_bp.route("/templates", methods=["GET"])
@jwt_required()
def list_templates():
    """GET /rubric-builder/templates — list all template rubrics."""
    templates = Rubric.query.filter_by(is_template=True).all()
    result = [_serialize_rubric_full(t) for t in templates]
    return jsonify({"templates": result}), 200


@rubric_builder_bp.route("/templates/<int:template_id>/apply/<int:assignment_id>", methods=["POST"])
@jwt_required()
def apply_template(template_id, assignment_id):
    """POST /rubric-builder/templates/<id>/apply/<id> — apply template to assignment."""
    template = Rubric.get_by_id(template_id)
    if template is None:
        return jsonify({"msg": "Template not found"}), 404

    existing = Rubric.get_rubric_by_assignment(assignment_id)
    if existing is not None:
        CriteriaDescription.query.filter_by(rubricID=existing.id).delete()
        db.session.delete(existing)
        db.session.flush()

    new_rubric = Rubric(assignmentID=assignment_id)
    new_rubric.template_name = template.template_name
    new_rubric.is_template = False
    db.session.add(new_rubric)
    db.session.flush()

    template_criteria = (
        CriteriaDescription.query
        .filter_by(rubricID=template.id)
        .order_by(CriteriaDescription.position)
        .all()
    )
    for tc in template_criteria:
        cd = CriteriaDescription(
            rubricID=new_rubric.id,
            question=tc.question,
            scoreMax=tc.scoreMax,
        )
        cd.description = tc.description or ""
        cd.weight = tc.weight or 0
        cd.position = tc.position
        db.session.add(cd)

    db.session.commit()
    return jsonify({"rubric": _serialize_rubric_full(new_rubric)}), 201

"""
Review controller for the peer evaluation app.
Provides the endpoint for submitting rubric-based peer reviews.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import User, Assignment, Review, Criterion, Group_Members
from api.models.rubric_model import Rubric
from api.models.criteria_description_model import CriteriaDescription

review_bp = Blueprint("review_submit", __name__, url_prefix="/api/reviews")


@review_bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_review():
    """
    POST /api/reviews/submit
    Submit a rubric-based peer review.
    Request body:
    {
      "assignment_id": int,
      "reviewee_id": int,
      "criteria": [
        { "criteria_description_id": int, "grade": int, "comments": str }
      ]
    }
    Validations:
    1. Reviewer != reviewee (no self-reviews)
    2. Assignment exists
    3. Reviewer is in the same group as reviewee
    4. No duplicate review (same reviewer + reviewee + assignment)
    """
    email = get_jwt_identity()
    reviewer = User.get_by_email(email)
    if reviewer is None:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    assignment_id = data.get("assignment_id")
    reviewee_id = data.get("reviewee_id")
    criteria_data = data.get("criteria", [])

    if not assignment_id or not reviewee_id:
        return jsonify({"msg": "assignment_id and reviewee_id are required"}), 400

    # 1. No self-reviews
    if reviewer.id == reviewee_id:
        return jsonify({"msg": "You cannot review yourself"}), 400

    # 2. Assignment must exist
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # 3. Reviewer must be in the same group as reviewee for this assignment
    reviewer_membership = Group_Members.query.filter_by(
        userID=reviewer.id, assignmentID=assignment_id
    ).first()
    reviewee_membership = Group_Members.query.filter_by(
        userID=reviewee_id, assignmentID=assignment_id
    ).first()

    if reviewer_membership and reviewee_membership:
        if reviewer_membership.groupID != reviewee_membership.groupID:
            return jsonify({"msg": "Reviewer and reviewee are not in the same group"}), 403

    # If no group memberships exist, allow the review (groups may not be set up)

    # 4. No duplicate reviews
    if Review.review_exists(reviewer.id, reviewee_id, assignment_id):
        return jsonify({"msg": "You have already submitted a review for this student on this assignment"}), 409

    # Create the review record
    review = Review(
        assignmentID=assignment_id,
        reviewerID=reviewer.id,
        revieweeID=reviewee_id,
    )
    Review.create_review(review)

    # Create criterion records for each score
    for c in criteria_data:
        criterion = Criterion(
            reviewID=review.id,
            criterionRowID=c.get("criteria_description_id"),
            grade=c.get("grade"),
            comments=c.get("comments", ""),
        )
        Criterion.create_criterion(criterion)

    # Notify the reviewee about the new peer review
    from api.services.notification_service import create_notification
    create_notification(
        user_id=reviewee_id,
        type="review_received",
        title="New Peer Review",
        message=f"{reviewer.name} submitted a peer review for you in {assignment.name}.",
        link=f"/student/feedback/{assignment_id}",
    )

    # Notify the teacher so their activity feed updates
    teacher_id = assignment.course.teacherID
    create_notification(
        user_id=teacher_id,
        type="review_received",
        title="Review Submitted",
        message=f"{reviewer.name} submitted a peer review in {assignment.name}.",
        link=f"/assignments/{assignment_id}/reviews",
    )

    return jsonify({"msg": "Review submitted successfully", "review_id": review.id}), 201
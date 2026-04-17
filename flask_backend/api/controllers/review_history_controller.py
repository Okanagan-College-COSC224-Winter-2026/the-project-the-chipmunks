"""
Review History controller for the peer evaluation app.
Implements student-facing review history and score trend endpoints.

Endpoints:
    GET /review-history/my-reviews  — all reviews given and received by the student
    GET /review-history/my-trends   — score trend + class comparison data

Auth:   JWT cookie — get_jwt_identity() returns email → resolved to user.id
Reads:  Review, Criterion, Assignment, User — NO writes, NO schema changes.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, Review, User
from ..models.criterion_model import Criterion

review_history_bp = Blueprint("review_history", __name__, url_prefix="/review-history")


# ── Private helper ────────────────────────────────────────────────────────────

def _review_avg_score(review) -> float | None:
    """
    Return the average of all Criterion.grade values for this review.
    Returns None if the review has no graded criteria.
    criteria is a dynamic relationship — call .all() to load it.
    """
    grades = [c.grade for c in review.criteria.all() if c.grade is not None]
    if not grades:
        return None
    return round(sum(grades) / len(grades), 2)


# ============================================================
# GET /review-history/my-reviews
# All reviews given and received by the authenticated student
# ============================================================

@review_history_bp.route("/my-reviews", methods=["GET"])
@jwt_required()
def my_reviews():
    """
    Return all reviews the authenticated student has given and received,
    ordered newest-first by review id.

    score      = average of Criterion.grade for that review (null if none)
    other_student = the name of the other person in the review
    created_at = null (Review model has no timestamp column)

    Response 200:
        {
            "given":    [ { id, assignment_id, assignment_name,
                            other_student, score, role, created_at } ],
            "received": [ ... ]
        }
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    # Reviews this student gave (they were the reviewer)
    given_reviews = (
        Review.query
        .filter_by(reviewerID=user.id)
        .order_by(Review.id.desc())
        .all()
    )

    # Reviews this student received (they were the reviewee)
    received_reviews = (
        Review.query
        .filter_by(revieweeID=user.id)
        .order_by(Review.id.desc())
        .all()
    )

    def serialize(review, role: str) -> dict:
        assignment = Assignment.get_by_id(review.assignmentID)

        # For reviews I gave, show who I reviewed (the reviewee's name is fine —
        # the reviewer already knows who they reviewed).
        # For reviews I received, NEVER expose the reviewer's identity — anonymous.
        if role == "given":
            other = User.get_by_id(review.revieweeID)
            other_student = other.name if other else "Unknown"
        else:
            other_student = "Anonymous Peer"

        return {
            "id":              review.id,
            "assignment_id":   review.assignmentID,
            "assignment_name": assignment.name if assignment else "Unknown",
            "other_student":   other_student,
            "score":           _review_avg_score(review),
            "role":            role,
            "created_at":      None,   # Review model has no timestamp column
        }

    return jsonify({
        "given":    [serialize(r, "given")    for r in given_reviews],
        "received": [serialize(r, "received") for r in received_reviews],
    }), 200


# ============================================================
# GET /review-history/my-trends
# Score trend + class comparison for the authenticated student
# ============================================================

@review_history_bp.route("/my-trends", methods=["GET"])
@jwt_required()
def my_trends():
    """
    Return score trend data (my avg per assignment) and class comparison
    data (my avg vs class avg per assignment).

    my_avg    = avg of Criterion.grade on reviews where I am the reviewee
    class_avg = avg of Criterion.grade on ALL reviews for that assignment

    Returns empty lists if the student has no reviews received.

    Response 200:
        {
            "trend": [
                { assignment_id, assignment_name, my_avg, review_count }
            ],
            "comparison": [
                { assignment_name, my_avg, class_avg }
            ]
        }
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    # All reviews where this student was the reviewee
    received_reviews = Review.query.filter_by(revieweeID=user.id).all()

    if not received_reviews:
        return jsonify({"trend": [], "comparison": []}), 200

    # ── Build per-assignment score buckets for this student ───────────────────
    # { assignment_id: [grade, grade, ...] }
    my_scores_by_assignment: dict[int, list[float]] = {}
    for review in received_reviews:
        aid = review.assignmentID
        grades = [c.grade for c in review.criteria.all() if c.grade is not None]
        if aid not in my_scores_by_assignment:
            my_scores_by_assignment[aid] = []
        my_scores_by_assignment[aid].extend(grades)

    # ── Build trend list ──────────────────────────────────────────────────────
    trend = []
    for aid, grades in my_scores_by_assignment.items():
        if not grades:
            continue
        assignment = Assignment.get_by_id(aid)
        trend.append({
            "assignment_id":   aid,
            "assignment_name": assignment.name if assignment else f"Assignment {aid}",
            "my_avg":          round(sum(grades) / len(grades), 2),
            "review_count":    len(grades),
        })

    # Sort trend by assignment_id for a consistent chronological order
    trend.sort(key=lambda x: x["assignment_id"])

    # ── Build comparison list ─────────────────────────────────────────────────
    # For each assignment in the student's trend, get the class-wide avg
    comparison = []
    for item in trend:
        aid = item["assignment_id"]

        # All reviews for this assignment (all students)
        all_reviews = Review.query.filter_by(assignmentID=aid).all()
        all_grades = [
            c.grade
            for r in all_reviews
            for c in r.criteria.all()
            if c.grade is not None
        ]
        class_avg = round(sum(all_grades) / len(all_grades), 2) if all_grades else 0.0

        comparison.append({
            "assignment_name": item["assignment_name"],
            "my_avg":          item["my_avg"],
            "class_avg":       class_avg,
        })

    return jsonify({"trend": trend, "comparison": comparison}), 200

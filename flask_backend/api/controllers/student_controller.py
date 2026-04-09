"""
Student controller for the peer evaluation app.
Provides endpoints for student-specific data like grades and feedback.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models import User, User_Course, Assignment, Review, Criterion, CriteriaDescription, Rubric

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_student_grades(student_id):
    """
    For each course the student is enrolled in:
    - Get all assignments
    - Get all reviews where revieweeID = student_id
    - Get all criterion scores from those reviews
    - Calculate averages
    Returns list of course grade dictionaries
    """
    enrollments = User_Course.get_courses_by_student(student_id)
    courses = []

    for enrollment in enrollments:
        course = enrollment.course
        assignments = Assignment.get_by_class_id(course.id)
        total_assignments = len(assignments)
        graded_assignments = 0
        assignment_averages = []
        max_scores = []

        for assignment in assignments:
            reviews = Review.query.filter_by(
                assignmentID=assignment.id, revieweeID=student_id
            ).all()

            criterion_grades = []
            for review in reviews:
                criteria = Criterion.query.filter_by(reviewID=review.id).all()
                for c in criteria:
                    if c.grade is not None:
                        criterion_grades.append(c.grade)
                        if c.criterion_row and c.criterion_row.scoreMax is not None:
                            max_scores.append(c.criterion_row.scoreMax)

            if criterion_grades:
                graded_assignments += 1
                assignment_avg = sum(criterion_grades) / len(criterion_grades)
                assignment_averages.append(assignment_avg)

        if graded_assignments > 0:
            grade = round(sum(assignment_averages) / len(assignment_averages), 1)
            max_score = max(max_scores) if max_scores else None
            has_grades = True
        else:
            grade = None
            max_score = None
            has_grades = False

        courses.append(
            {
                "course_id": course.id,
                "course_name": course.name,
                "grade": grade,
                "max_score": max_score,
                "graded_assignments": graded_assignments,
                "total_assignments": total_assignments,
                "has_grades": has_grades,
            }
        )

    return courses


@student_bp.route("/grades", methods=["GET"])
@jwt_required()
def grades():
    """GET /student/grades — Returns per-course grade summaries for the student."""
    email = get_jwt_identity()
    user = User.get_by_email(email)

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    courses = get_student_grades(user.id)

    return jsonify({"student_id": user.id, "courses": courses}), 200


def get_assignment_feedback(assignment_id, student_id):
    """
    For a given assignment, aggregate all peer review feedback
    received by the student (revieweeID = student_id).

    Returns the response in the sprint plan format:
    {
        "assignment_name": str,
        "total_reviews": int,
        "criteria_feedback": [
            {
                "question": str,
                "avg_score": float,
                "max_score": int,
                "comments": [str]
            }
        ],
        "overall_avg": float
    }

    Reviewer identities are never exposed.
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return None

    reviews = Review.query.filter_by(
        assignmentID=assignment_id, revieweeID=student_id
    ).all()

    if not reviews:
        return {
            "assignment_id": assignment.id,
            "assignment_name": assignment.name or f"Assignment {assignment_id}",
            "total_reviews": 0,
            "criteria_feedback": [],
            "overall_avg": 0.0,
        }

    # Aggregate scores and comments per criteria_description
    criteria_map = {}

    for review in reviews:
        criteria = Criterion.query.filter_by(reviewID=review.id).all()
        for c in criteria:
            desc = c.criterion_row
            if desc is None:
                continue

            crit_id = desc.id
            if crit_id not in criteria_map:
                criteria_map[crit_id] = {
                    "question": desc.question or f"Criterion {crit_id}",
                    "score_max": desc.scoreMax or 0,
                    "scores": [],
                    "comments": [],
                }

            if c.grade is not None:
                criteria_map[crit_id]["scores"].append(c.grade)
            if c.comments and c.comments.strip():
                criteria_map[crit_id]["comments"].append(c.comments)

    # Build criteria_feedback list
    criteria_feedback = []
    all_avgs = []

    for crit_id, data in criteria_map.items():
        scores = data["scores"]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        criteria_feedback.append({
            "question": data["question"],
            "avg_score": average_score,
            "max_score": data["score_max"],
            "comments": data["comments"],
        })

        if scores:
            all_avgs.append(average_score)

    # Calculate overall average across all criteria
    overall_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0.0

    return {
        "assignment_id": assignment.id,
        "assignment_name": assignment.name or f"Assignment {assignment_id}",
        "total_reviews": len(reviews),
        "criteria_feedback": criteria_feedback,
        "overall_avg": overall_avg,
    }


@student_bp.route("/assignments/<int:assignment_id>/feedback", methods=["GET"])
@jwt_required()
def assignment_feedback(assignment_id):
    """
    GET /student/assignments/<assignment_id>/feedback
    Returns aggregated anonymous feedback for the logged-in student
    for the given assignment.
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    feedback = get_assignment_feedback(assignment_id, user.id)

    return jsonify(feedback), 200
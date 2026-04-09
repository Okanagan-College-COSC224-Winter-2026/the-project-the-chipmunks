"""
Student controller for the peer evaluation app.
Provides endpoints for student-specific data like grades and feedback.
"""

import os
from flask import Blueprint, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models import User, User_Course, Assignment, Review, Criterion, CriteriaDescription, Rubric, Group_Members, ReviewFile, ConclusionFile

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

@student_bp.route("/assignments/<int:assignment_id>/team-submissions", methods=["GET"])
@jwt_required()
def team_submissions(assignment_id):
    """
    Returns all submitted files from the logged-in student's group members
    for the given assignment. The caller's own files are excluded.

    Response 200: { assignment_id, assignment_name, group_members: [...] }
    Response 403: student is not in a group for this assignment
    Response 404: assignment not found
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # Find the student's group membership for this assignment
    membership = Group_Members.query.filter_by(
        userID=user.id, assignmentID=assignment_id
    ).first()
    if membership is None:
        return jsonify({"msg": "You are not in a group for this assignment"}), 403

    # Get all members of the same group, excluding the current user
    all_members = Group_Members.query.filter_by(
        groupID=membership.groupID, assignmentID=assignment_id
    ).all()
    other_members = [m for m in all_members if m.userID != user.id]

    # Conclusion files are assignment-level (not per-user), include once on first member
    conclusion_files = ConclusionFile.get_by_assignment(assignment_id)

    group_members_data = []
    for idx, member in enumerate(other_members):
        member_user = User.get_by_id(member.userID)
        if member_user is None:
            continue

        # Review files: files attached to reviews where this member was the reviewer
        review_files_query = (
            ReviewFile.query
            .join(Review, Review.id == ReviewFile.reviewID)
            .filter(
                Review.reviewerID == member.userID,
                Review.assignmentID == assignment_id,
            )
            .all()
        )

        review_files_data = [
            {
                "file_id":     rf.id,
                "filename":    rf.filename,
                "uploaded_at": rf.uploaded_at.isoformat() if rf.uploaded_at else None,
                "size_bytes":  os.path.getsize(rf.file_path) if os.path.isfile(rf.file_path) else 0,
            }
            for rf in review_files_query
        ]

        # Conclusion files attached to first member card only (they are assignment-level)
        conclusion_files_data = []
        if idx == 0:
            conclusion_files_data = [
                {
                    "file_id":     cf.id,
                    "filename":    cf.filename,
                    "uploaded_at": cf.uploaded_at.isoformat() if cf.uploaded_at else None,
                }
                for cf in conclusion_files
            ]

        group_members_data.append({
            "member_id":        member_user.id,
            "member_name":      member_user.name,
            "review_files":     review_files_data,
            "conclusion_files": conclusion_files_data,
        })

    return jsonify({
        "assignment_id":   assignment.id,
        "assignment_name": assignment.name,
        "group_members":   group_members_data,
    }), 200


# ============================================================
# GET /student/review-file/<file_id>/download
# Stream a review file — only if requester is in the same group
# ============================================================

@student_bp.route("/review-file/<int:file_id>/download", methods=["GET"])
@jwt_required()
def download_team_review_file(file_id):
    """
    Streams the file identified by file_id.
    Returns 403 if the requesting student is not in the same group as the file owner.
    Returns 404 if the file does not exist.
    """
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    review_file = ReviewFile.get_by_id(file_id)
    if review_file is None:
        return jsonify({"msg": "File not found"}), 404

    # Security check: requester must be in the same group as the file owner
    assignment_id = review_file.review.assignmentID
    file_owner_id = review_file.uploaderID

    requester_membership = Group_Members.query.filter_by(
        userID=user.id, assignmentID=assignment_id
    ).first()
    owner_membership = Group_Members.query.filter_by(
        userID=file_owner_id, assignmentID=assignment_id
    ).first()

    if (
        requester_membership is None
        or owner_membership is None
        or requester_membership.groupID != owner_membership.groupID
    ):
        return jsonify({"msg": "You do not have permission to download this file"}), 403

    if not os.path.isfile(review_file.file_path):
        return jsonify({"msg": "File not found on server"}), 404

    directory = os.path.dirname(review_file.file_path)
    basename = os.path.basename(review_file.file_path)

    return send_from_directory(
        directory,
        basename,
        as_attachment=True,
        download_name=review_file.filename,
    )

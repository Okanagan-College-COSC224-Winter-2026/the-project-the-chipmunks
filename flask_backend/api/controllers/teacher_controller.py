"""
Teacher Review Dashboard controller.
Implements US13 (view review submissions), US14 (add conclusion note),
and US7/US8 extension (assignment analytics & CSV export).

Endpoints:
    GET  /teacher/assignments/<assignment_id>/reviews
    GET  /teacher/assignments/<assignment_id>/reviews/<review_id>
    POST /teacher/reviews/<review_id>/conclusion
    GET  /teacher/assignments/<assignment_id>/analytics
    GET  /teacher/assignments/<assignment_id>/export
    GET  /teacher/assignments/<assignment_id>/export-pdf
"""

import csv
import io
import statistics

from io import BytesIO
from flask import Blueprint, Response, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity

from ..models import (
    Assignment,
    CriteriaDescription,
    Criterion,
    CourseGroup,
    Group_Members,
    Review,
    Rubric,
    User,
    Course,
    User_Course,
)
from ..models.conclusion_model import Conclusion
from ..models.db import db
from .auth_controller import jwt_teacher_required
from ..services.pdf_report_service import generate_assignment_report
from sqlalchemy import func

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


# ── Private helper ────────────────────────────────────────────────────────────

def _review_total_score(review) -> int:
    """
    Sum the grades across all Criterion rows for this review.

    This project stores per-criterion scores in the Criterion table
    (columns: grade, comments) linked back to CriteriaDescription
    for the question text and scoreMax.
    criteria is a dynamic relationship so we call .all() to load it.
    """
    return sum(
        (c.grade or 0)
        for c in review.criteria.all()
    )


# ============================================================
# GET /teacher/assignments/<assignment_id>/reviews
# List all reviews for an assignment (teacher/admin only)
# ============================================================

@teacher_bp.route("/assignments/<int:assignment_id>/reviews", methods=["GET"])
@jwt_teacher_required
def list_assignment_reviews(assignment_id):
    """
    Return a summary list of all peer reviews submitted for an assignment.

    Query parameters:
        group_id (int, optional) — filter to reviewees who belong to this group
        sort     (str, optional) — 'id' (default) or 'score' (descending)

    Response 200:
        [
            {
                "review_id":      int,
                "reviewer_id":    int,
                "reviewee_id":    int,
                "total_score":    int,
                "has_conclusion": bool
            },
            ...
        ]

    Response 404: assignment not found
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    group_id = request.args.get("group_id", None, type=int)
    sort_by  = request.args.get("sort", "id")

    # ── Base query ────────────────────────────────────────────────────────────
    query = Review.query.filter_by(assignmentID=assignment_id)

    # ── Optional group filter ─────────────────────────────────────────────────
    if group_id is not None:
        # Resolve the group, return 404 if it doesn't exist
        group = CourseGroup.get_by_id(group_id)
        if group is None:
            return jsonify({"msg": "Group not found"}), 404

        member_ids = [
            m.userID
            for m in Group_Members.query.filter_by(groupID=group_id).all()
        ]
        query = query.filter(Review.revieweeID.in_(member_ids))

    reviews = query.all()

    # ── Optional sort ─────────────────────────────────────────────────────────
    if sort_by == "score":
        reviews = sorted(reviews, key=_review_total_score, reverse=True)

    return jsonify([
        {
            "review_id":      r.id,
            "reviewer_id":    r.reviewerID,
            "reviewee_id":    r.revieweeID,
            "total_score":    _review_total_score(r),
            "has_conclusion": r.conclusion is not None,
        }
        for r in reviews
    ]), 200


# ============================================================
# GET /teacher/assignments/<assignment_id>/reviews/<review_id>
# Full detail for one review: criteria breakdown + conclusion
# ============================================================

@teacher_bp.route(
    "/assignments/<int:assignment_id>/reviews/<int:review_id>",
    methods=["GET"],
)
@jwt_teacher_required
def get_review_detail(assignment_id, review_id):
    """
    Return the full detail of a single peer review, including each
    criterion's score and comment, and the conclusion note if one exists.

    Response 200:
        {
            "review_id":   int,
            "reviewer_id": int,
            "reviewee_id": int,
            "criteria": [
                {
                    "criterion_id":   int,
                    "criterion_name": str,
                    "score":          int | null,
                    "score_max":      int | null,
                    "comment":        str
                },
                ...
            ],
            "conclusion": { ...to_dict() } | null
        }

    Response 404: assignment or review not found
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    review = Review.query.filter_by(
        id=review_id, assignmentID=assignment_id
    ).first()
    if review is None:
        return jsonify({"msg": "Review not found"}), 404

    # ── Build criteria breakdown ──────────────────────────────────────────────
    # Each Criterion row has a grade + comments, and a FK to CriteriaDescription
    # which holds the human-readable question and scoreMax.
    criteria_breakdown = [
        {
            "criterion_id":   c.id,
            "criterion_name": (
                c.criterion_row.question if c.criterion_row else ""
            ),
            "score":          c.grade,
            "score_max":      (
                c.criterion_row.scoreMax if c.criterion_row else None
            ),
            "comment":        c.comments or "",
        }
        for c in review.criteria.all()
    ]

    conclusion = Conclusion.get_by_review(review_id)

    return jsonify({
        "review_id":   review.id,
        "reviewer_id": review.reviewerID,
        "reviewee_id": review.revieweeID,
        "criteria":    criteria_breakdown,
        "conclusion":  conclusion.to_dict() if conclusion else None,
    }), 200


# ============================================================
# POST /teacher/reviews/<review_id>/conclusion
# Create or update the conclusion note for a review (upsert)
# ============================================================

@teacher_bp.route("/reviews/<int:review_id>/conclusion", methods=["POST"])
@jwt_teacher_required
def upsert_conclusion(review_id):
    """
    Create or update the instructor note (Conclusion) on a peer review.
    Behaves as an upsert: a second POST to the same review_id updates
    the existing note rather than creating a duplicate.

    Request body (JSON):
        { "note": str }

    Response 200: conclusion.to_dict()
    Response 400: empty note
    Response 404: review not found
    """
    review = Review.get_by_id(review_id)
    if review is None:
        return jsonify({"msg": "Review not found"}), 404

    note = (request.json or {}).get("note", "").strip()
    if not note:
        return jsonify({"error": "Note cannot be empty"}), 400

    # ── Resolve the teacher from the JWT cookie ───────────────────────────────
    email = get_jwt_identity()
    teacher = User.get_by_email(email)
    if teacher is None:
        return jsonify({"msg": "User not found"}), 404

    # ── Upsert ────────────────────────────────────────────────────────────────
    existing = Conclusion.get_by_review(review_id)
    if existing:
        existing.note = note
        existing.update()
    else:
        existing = Conclusion(
            reviewID=review_id,
            teacherID=teacher.id,
            note=note,
        )
        Conclusion.create(existing)

    return jsonify(existing.to_dict()), 200


# ============================================================
# GET /teacher/assignments/<assignment_id>/analytics
# Per-criterion averages, completion rate, outlier detection
# ============================================================

@teacher_bp.route("/assignments/<int:assignment_id>/analytics", methods=["GET"])
@jwt_teacher_required
def assignment_analytics(assignment_id):
    """
    Return analytics for an assignment: completion rate, per-criterion
    average scores, and flagged outlier reviews (>2 std deviations).

    Response 200:
        {
            "assignment_id":   int,
            "assignment_name": str,
            "completion_pct":  float,
            "total_students":  int,
            "submitted":       int,
            "criteria":        [ { criterion_id, criterion_name, score_max,
                                   avg_score, response_count } ],
            "outliers":        [ { review_id, reviewer_id, reviewee_id,
                                   total_score, deviation } ]
        }

    Response 404: assignment not found
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # --- Completion rate ---
    total_students = (
        db.session.query(Group_Members.userID)
        .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
        .filter(CourseGroup.assignmentID == assignment_id)
        .distinct()
        .count()
    )
    submitted = (
        Review.query
        .filter_by(assignmentID=assignment_id)
        .with_entities(Review.reviewerID)
        .distinct()
        .count()
    )
    completion_pct = (
        round((submitted / total_students * 100), 1) if total_students else 0
    )

    # --- Per-criterion averages ---
    crit_descs = (
        CriteriaDescription.query
        .join(Rubric, Rubric.id == CriteriaDescription.rubricID)
        .filter(Rubric.assignmentID == assignment_id)
        .all()
    )

    criterion_data = []
    all_review_totals = []
    for cd in crit_descs:
        scores = [
            c.grade
            for c in Criterion.query.filter_by(criterionRowID=cd.id).all()
            if c.grade is not None
        ]
        avg = round(statistics.mean(scores), 2) if scores else 0
        criterion_data.append({
            "criterion_id": cd.id,
            "criterion_name": cd.question,
            "score_max": cd.scoreMax,
            "avg_score": avg,
            "response_count": len(scores),
        })
        all_review_totals.extend(scores)

    # --- Outlier detection (>2 std deviations from mean) ---
    outliers = []
    if len(all_review_totals) >= 2:
        mean = statistics.mean(all_review_totals)
        stdev = statistics.stdev(all_review_totals)
        threshold = 2 * stdev

        reviews = Review.query.filter_by(assignmentID=assignment_id).all()
        for rev in reviews:
            total = sum(
                (c.grade or 0) for c in rev.criteria.all()
            )
            if abs(total - mean) > threshold:
                outliers.append({
                    "review_id": rev.id,
                    "reviewer_id": rev.reviewerID,
                    "reviewee_id": rev.revieweeID,
                    "total_score": total,
                    "deviation": round(total - mean, 2),
                })

    return jsonify({
        "assignment_id": assignment_id,
        "assignment_name": assignment.name,
        "completion_pct": completion_pct,
        "total_students": total_students,
        "submitted": submitted,
        "criteria": criterion_data,
        "outliers": outliers,
    }), 200


# ============================================================
# GET /teacher/assignments/<assignment_id>/export
# CSV export of all raw review data for an assignment
# ============================================================

@teacher_bp.route("/assignments/<int:assignment_id>/export", methods=["GET"])
@jwt_teacher_required
def export_reviews_csv(assignment_id):
    """
    Export all review scores for an assignment as a downloadable CSV file.

    Columns: review_id, reviewer_id, reviewee_id, criterion, score,
             max_score, comment

    Response 200: text/csv attachment
    Response 404: assignment not found
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    reviews = Review.query.filter_by(assignmentID=assignment_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "review_id", "reviewer_id", "reviewee_id",
        "criterion", "score", "max_score", "comment",
    ])

    for rev in reviews:
        for c in rev.criteria.all():
            writer.writerow([
                rev.id,
                rev.reviewerID,
                rev.revieweeID,
                c.criterion_row.question if c.criterion_row else "",
                c.grade,
                c.criterion_row.scoreMax if c.criterion_row else "",
                c.comments or "",
            ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f"attachment;filename=assignment_{assignment_id}_reviews.csv"
        },
    )


# ============================================================
# GET /teacher/assignments/<assignment_id>/export-pdf
# PDF export of assignment review results
# ============================================================

@teacher_bp.route("/assignments/<int:assignment_id>/export-pdf", methods=["GET"])
@jwt_teacher_required
def export_assignment_pdf(assignment_id):
    """
    Generate and return a formatted PDF report for an assignment.
    Returns 200 with application/pdf for teachers.
    Returns 403 for students (handled by jwt_teacher_required).
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    assignment_info = {
        "title": assignment.name,
        "course_name": assignment.course.name if assignment.course else "Unknown Course",
    }

    # Fetch all students in this assignment's groups
    student_id_rows = (
        db.session.query(Group_Members.userID)
        .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
        .filter(CourseGroup.assignmentID == assignment_id)
        .distinct()
        .all()
    )
    student_ids = [row[0] for row in student_id_rows]

    students_data = []
    for sid in student_ids:
        student = db.session.get(User, sid)
        if not student:
            continue

        reviews_received = Review.query.filter_by(
            assignmentID=assignment_id, revieweeID=sid
        ).all()

        reviews_given_count = Review.query.filter_by(
            assignmentID=assignment_id, reviewerID=sid
        ).count()

        all_scores = [_review_total_score(r) for r in reviews_received]
        avg_score = (sum(all_scores) / len(all_scores)) if all_scores else None

        has_submitted = Review.query.filter_by(
            assignmentID=assignment_id, reviewerID=sid
        ).first() is not None
        completion_status = "Complete" if has_submitted else "Incomplete"

        students_data.append({
            "name": student.name,
            "avg_score": avg_score,
            "reviews_received": len(reviews_received),
            "reviews_given": reviews_given_count,
            "completion_status": completion_status,
        })

    pdf_bytes = generate_assignment_report(assignment_info, students_data)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{assignment.name.replace(' ', '_')}_Report.pdf",
    )

# ============================================================
# GET /teacher/classes/<course_id>/progress
# Per-student, per-assignment progress across a course
# ============================================================

@teacher_bp.route("/classes/<int:course_id>/progress", methods=["GET"])
@jwt_teacher_required
def course_student_progress(course_id):
    """
    Return a per-student, per-assignment breakdown of group membership,
    review submission counts, and average rubric score for every student
    enrolled in the course.

    Response 200:
        {
            "course_id":   int,
            "course_name": str,
            "assignments": [{ "id": int, "name": str }],
            "students": [
                {
                    "user_id": int,
                    "name":    str,
                    "email":   str,
                    "per_assignment": {
                        "<assignment_id>": {
                            "in_group":         bool,
                            "reviews_given":    int,
                            "reviews_received": int,
                            "avg_score":        float | null
                        }
                    }
                }
            ]
        }

    Response 403: not a teacher/admin (handled by decorator)
    Response 404: course not found
    """
    course = Course.get_by_id(course_id)
    if course is None:
        return jsonify({"msg": "Course not found"}), 404

    # ── All assignments for this course ───────────────────────────────────────
    assignments = Assignment.query.filter_by(courseID=course_id).all()
    assignment_ids = [a.id for a in assignments]

    # ── All students enrolled in the course ───────────────────────────────────
    enrolled = (
        db.session.query(User)
        .join(User_Course, User_Course.userID == User.id)
        .filter(User_Course.courseID == course_id)
        .filter(User.role == "student")
        .all()
    )

    # ── Pre-fetch group membership rows for this course's assignments ─────────
    membership_set = set(
        db.session.query(Group_Members.userID, Group_Members.assignmentID)
        .filter(Group_Members.assignmentID.in_(assignment_ids))
        .all()
    ) if assignment_ids else set()

    # ── Pre-fetch review given counts ─────────────────────────────────────────
    given_rows = (
        db.session.query(Review.reviewerID, Review.assignmentID, func.count(Review.id))
        .filter(Review.assignmentID.in_(assignment_ids))
        .group_by(Review.reviewerID, Review.assignmentID)
        .all()
    ) if assignment_ids else []
    given_map = {(r, a): cnt for r, a, cnt in given_rows}

    # ── Pre-fetch review received counts ──────────────────────────────────────
    received_rows = (
        db.session.query(Review.revieweeID, Review.assignmentID, func.count(Review.id))
        .filter(Review.assignmentID.in_(assignment_ids))
        .group_by(Review.revieweeID, Review.assignmentID)
        .all()
    ) if assignment_ids else []
    received_map = {(r, a): cnt for r, a, cnt in received_rows}

    # ── Pre-fetch avg_score per (revieweeID, assignmentID) ────────────────────
    avg_rows = (
        db.session.query(
            Review.revieweeID,
            Review.assignmentID,
            func.avg(Criterion.grade),
        )
        .join(Criterion, Criterion.reviewID == Review.id)
        .filter(Review.assignmentID.in_(assignment_ids))
        .filter(Criterion.grade.isnot(None))
        .group_by(Review.revieweeID, Review.assignmentID)
        .all()
    ) if assignment_ids else []
    avg_map = {(r, a): avg for r, a, avg in avg_rows}

    # ── Build student list ────────────────────────────────────────────────────
    students_data = []
    for student in enrolled:
        per_assignment = {}
        for a in assignments:
            in_group = (student.id, a.id) in membership_set
            reviews_given = given_map.get((student.id, a.id), 0)
            reviews_received = received_map.get((student.id, a.id), 0)
            raw_avg = avg_map.get((student.id, a.id))
            avg_score = round(float(raw_avg), 2) if raw_avg is not None else None

            per_assignment[str(a.id)] = {
                "in_group":          in_group,
                "reviews_given":     reviews_given,
                "reviews_received":  reviews_received,
                "avg_score":         avg_score,
            }

        students_data.append({
            "user_id":        student.id,
            "name":           student.name,
            "email":          student.email,
            "per_assignment": per_assignment,
        })

    return jsonify({
        "course_id":   course.id,
        "course_name": course.name,
        "assignments": [{"id": a.id, "name": a.name} for a in assignments],
        "students":    students_data,
    }), 200


# ============================================================
# GET /teacher/assignments/<id>/completion
# Per-student review completion status for an assignment
# ============================================================

@teacher_bp.route("/assignments/<int:assignment_id>/completion", methods=["GET"])
@jwt_teacher_required
def assignment_completion(assignment_id):
    """
    Return the review completion status for every student in the assignment's groups.

    Response 200:
        {
            "assignment_id":   int,
            "assignment_name": str,
            "total":           int,
            "submitted":       int,
            "completion_pct":  float,
            "students": [
                {
                    "user_id":       int,
                    "name":          str,
                    "status":        "Complete" | "Incomplete",
                    "reviews_given": int,
                    "reviewed":      [{ "reviewee_id": int, "reviewee_name": str }]
                }
            ]
        }
    """
    assignment = Assignment.get_by_id(assignment_id)
    if assignment is None:
        return jsonify({"msg": "Assignment not found"}), 404

    # All students in a group for this assignment
    memberships = (
        db.session.query(Group_Members.userID)
        .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
        .filter(CourseGroup.assignmentID == assignment_id)
        .distinct()
        .all()
    )
    student_ids = [m.userID for m in memberships]

    # All reviews for this assignment, keyed by reviewerID
    all_reviews = Review.query.filter_by(assignmentID=assignment_id).all()
    reviews_by_reviewer: dict = {}
    for rev in all_reviews:
        reviews_by_reviewer.setdefault(rev.reviewerID, []).append(rev)

    # Build per-student data
    students_data = []
    for sid in student_ids:
        student = User.get_by_id(sid)
        if student is None:
            continue

        given = reviews_by_reviewer.get(sid, [])
        reviewed_list = []
        for rev in given:
            reviewee = User.get_by_id(rev.revieweeID)
            reviewed_list.append({
                "reviewee_id":   rev.revieweeID,
                "reviewee_name": reviewee.name if reviewee else f"#{rev.revieweeID}",
            })

        students_data.append({
            "user_id":       student.id,
            "name":          student.name,
            "status":        "Complete" if given else "Incomplete",
            "reviews_given": len(given),
            "reviewed":      reviewed_list,
        })

    # Sort: incomplete first, then by name
    students_data.sort(key=lambda s: (s["status"] == "Complete", s["name"]))

    total = len(students_data)
    submitted = sum(1 for s in students_data if s["status"] == "Complete")
    completion_pct = round(submitted / total * 100, 1) if total else 0

    return jsonify({
        "assignment_id":  assignment_id,
        "assignment_name": assignment.name,
        "total":          total,
        "submitted":      submitted,
        "completion_pct": completion_pct,
        "students":       students_data,
    }), 200

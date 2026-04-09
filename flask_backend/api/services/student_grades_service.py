from sqlalchemy import func
from api.models.db import db
from api.models.user_course_model import User_Course
from api.models.course_model import Course
from api.models.assignment_model import Assignment
from api.models.review_model import Review
from api.models.criterion_model import Criterion

MAX_SCORE_DEFAULT = 5.0


def get_student_grades(student_id: int) -> list[dict]:
    """
    For each course the student is enrolled in:
    - Count total assignments
    - Find reviews where revieweeID = student_id
    - Average Criterion.grade across those reviews (ignoring null grades)
    - Count how many distinct assignments have at least one graded criterion
    """
    enrolled = (
        db.session.query(Course.id, Course.name)
        .join(User_Course, User_Course.courseID == Course.id)
        .filter(User_Course.userID == student_id)
        .all()
    )

    results: list[dict] = []

    for course_id, course_name in enrolled:
        total_assignments = (
            db.session.query(func.count(Assignment.id))
            .filter(Assignment.courseID == course_id)
            .scalar()
        ) or 0

        # Average grade across all criteria for this student's received reviews in this course
        avg_grade = (
            db.session.query(func.avg(Criterion.grade))
            .join(Review, Review.id == Criterion.reviewID)
            .join(Assignment, Assignment.id == Review.assignmentID)
            .filter(Assignment.courseID == course_id)
            .filter(Review.revieweeID == student_id)
            .filter(Criterion.grade.isnot(None))
            .scalar()
        )

        # Count distinct assignments that have at least one graded criterion for this student
        graded_assignments = (
            db.session.query(func.count(func.distinct(Assignment.id)))
            .join(Review, Review.assignmentID == Assignment.id)
            .join(Criterion, Criterion.reviewID == Review.id)
            .filter(Assignment.courseID == course_id)
            .filter(Review.revieweeID == student_id)
            .filter(Criterion.grade.isnot(None))
            .scalar()
        ) or 0

        has_grades = (avg_grade is not None) and (graded_assignments > 0)

        results.append(
            {
                "course_id": int(course_id),
                "course_name": course_name,
                "grade": round(float(avg_grade), 2) if has_grades else None,
                "max_score": float(MAX_SCORE_DEFAULT) if has_grades else None,
                "graded_assignments": int(graded_assignments),
                "total_assignments": int(total_assignments),
                "has_grades": bool(has_grades),
            }
        )

    return results

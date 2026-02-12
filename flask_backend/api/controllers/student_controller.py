from flask import Blueprint, jsonify

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.get("/grades")
def get_student_grades_for_current_student():
    """
    Temporary: public endpoint for testing.
    """
    student_id = 1  # hard-coded for now

    grades_data = {
        "student_id": student_id,
        "courses": []
    }

    return jsonify(grades_data), 200

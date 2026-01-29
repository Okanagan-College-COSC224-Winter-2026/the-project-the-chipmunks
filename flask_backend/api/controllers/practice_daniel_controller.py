"""
Practice Controller
Handles the /practice/test endpoint for COSC 224 lab
"""

from flask import Blueprint, jsonify

# Create a Blueprint for practice routes
practice_bp = Blueprint('practice', __name__, url_prefix='/practice')


@practice_bp.route('/test', methods=['GET'])
def get_practice_test():
    """
    GET /practice/test
    Returns a JSON object with course information
    
    Returns:
        JSON: {"course": "cosc 224"}
        Status: 200
    """
    return jsonify({
        "course": "cosc 224"
    }), 200
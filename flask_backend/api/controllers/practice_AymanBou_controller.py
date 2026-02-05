from flask import Blueprint, jsonify

# Blueprint following the project pattern
bp = Blueprint("practice", __name__, url_prefix="/api/practice")


@bp.route("/test", methods=["GET"])
def practice_test():
    return jsonify({"course": "cosc 224"}), 200

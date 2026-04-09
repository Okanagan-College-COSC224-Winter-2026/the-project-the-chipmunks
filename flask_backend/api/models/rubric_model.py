"""
Rubric model for the peer evaluation app.
"""

from .db import db


class Rubric(db.Model):
    """Rubric model representing evaluation criteria"""

    __tablename__ = "Rubric"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    canComment = db.Column(db.Boolean, nullable=False, default=True)
    is_template = db.Column(db.Boolean, default=False, nullable=False)
    template_name = db.Column(db.String(200), nullable=True)

    # relationships
    assignment = db.relationship("Assignment", back_populates="rubrics")
    criteria_descriptions = db.relationship(
        "CriteriaDescription", back_populates="rubric", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, assignmentID, canComment=True):
        self.assignmentID = assignmentID
        self.canComment = canComment

    def __repr__(self):
        return f"<Rubric id={self.id} assignmentID={self.assignmentID}>"

    @classmethod
    def get_by_id(cls, rubric_id):
        """Get rubric by ID"""
        return db.session.get(cls, int(rubric_id))

    @classmethod
    def get_rubric_by_assignment(cls, assignment_id: int):
        """
        Get the rubric for a given assignment ID.
        Returns None if no rubric exists for that assignment.
        """
        return cls.query.filter_by(assignmentID=int(assignment_id)).first()

    @classmethod
    def create_rubric(cls, rubric):
        """Add a new rubric to the database"""
        db.session.add(rubric)
        db.session.commit()
        return rubric

    def update(self):
        """Update rubric in the database"""
        db.session.commit()

    def delete(self):
        """Delete rubric from the database"""
        db.session.delete(self)
        db.session.commit()
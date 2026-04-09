"""
CriteriaDescription model for the peer evaluation app.
"""

from .db import db


class CriteriaDescription(db.Model):
    """CriteriaDescription model representing evaluation criteria descriptions"""

    __tablename__ = "Criteria_Description"

    id = db.Column(db.Integer, primary_key=True)
    rubricID = db.Column(db.Integer, db.ForeignKey("Rubric.id"), nullable=False, index=True)
    question = db.Column(db.String(255), nullable=True)
    scoreMax = db.Column(db.Integer, nullable=True)
    hasScore = db.Column(db.Boolean, nullable=False, default=True)
    description = db.Column(db.String(255), nullable=True, default="")
    weight = db.Column(db.Float, nullable=True, default=0)
    position = db.Column(db.Integer, default=0, nullable=False)

    # relationships
    rubric = db.relationship("Rubric", back_populates="criteria_descriptions")
    criteria = db.relationship(
        "Criterion", back_populates="criterion_row", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, rubricID, question, scoreMax, hasScore=True):
        self.rubricID = rubricID
        self.question = question
        self.scoreMax = scoreMax
        self.hasScore = hasScore

    def __repr__(self):
        return f"<CriteriaDescription id={self.id} rubric={self.rubricID}>"

    @classmethod
    def get_by_id(cls, criteria_id):
        """Get criteria description by ID"""
        return db.session.get(cls, int(criteria_id))

    @classmethod
    def get_criteria_by_rubric(cls, rubric_id: int):
        """
        Get all criteria descriptions for a given rubric.
        Returns an empty list if none exist.
        """
        return cls.query.filter_by(rubricID=int(rubric_id)).all()

    @classmethod
    def create_criteria_description(cls, criteria_description):
        """Add a new criteria description to the database"""
        db.session.add(criteria_description)
        db.session.commit()
        return criteria_description

    def update(self):
        """Update criteria description in the database"""
        db.session.commit()

    def delete(self):
        """Delete criteria description from the database"""
        db.session.delete(self)
        db.session.commit()
"""
Conclusion model for the peer evaluation app.
Stores a teacher's private instructor note on a peer review submission.
One Conclusion per Review (unique constraint on reviewID).
"""

from datetime import datetime, timezone

from .db import db


class Conclusion(db.Model):
    """Teacher-written note attached to a single peer review."""

    __tablename__ = "Conclusion"

    id = db.Column(db.Integer, primary_key=True)
    reviewID = db.Column(
        db.Integer,
        db.ForeignKey("Review.id"),
        nullable=False,
        unique=True,   # one conclusion per review
        index=True,
    )
    teacherID = db.Column(
        db.Integer,
        db.ForeignKey("User.id"),
        nullable=False,
        index=True,
    )
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # relationships
    review = db.relationship("Review", back_populates="conclusion")
    teacher = db.relationship("User", foreign_keys=[teacherID])

    def __init__(self, reviewID, teacherID, note):
        self.reviewID = reviewID
        self.teacherID = teacherID
        self.note = note

    def __repr__(self):
        return f"<Conclusion id={self.id} reviewID={self.reviewID}>"

    def to_dict(self):
        """Serialise to the shape the frontend expects."""
        return {
            "id": self.id,
            "review_id": self.reviewID,
            "teacher_id": self.teacherID,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ── Class methods ─────────────────────────────────────────────────────────

    @classmethod
    def get_by_id(cls, conclusion_id):
        return db.session.get(cls, int(conclusion_id))

    @classmethod
    def get_by_review(cls, review_id):
        """Return the Conclusion for a given review, or None."""
        return cls.query.filter_by(reviewID=int(review_id)).first()

    @classmethod
    def create(cls, conclusion):
        db.session.add(conclusion)
        db.session.commit()
        return conclusion

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

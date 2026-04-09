"""
Review model for the peer evaluation app.
"""
from sqlalchemy.orm import joinedload
from .db import db

class Review(db.Model):
    """Review model representing peer evaluations"""
    __tablename__ = "Review"
    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    reviewerID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    revieweeID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    # relationships - using lazy='joined' for commonly accessed foreign entities
    assignment = db.relationship("Assignment", back_populates="reviews", lazy="joined")
    reviewer = db.relationship(
        "User", foreign_keys=[reviewerID], back_populates="reviews_made", lazy="joined"
    )
    reviewee = db.relationship(
        "User", foreign_keys=[revieweeID], back_populates="reviews_received", lazy="joined"
    )
    criteria = db.relationship(
        "Criterion", back_populates="review", cascade="all, delete-orphan", lazy="dynamic"
    )
    files = db.relationship(
        "ReviewFile", back_populates="review", cascade="all, delete-orphan", lazy="dynamic"
    )
    # Task 3 — teacher conclusion note (one-to-one, uselist=False)
    conclusion = db.relationship(
        "Conclusion",
        back_populates="review",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __init__(self, assignmentID, reviewerID, revieweeID):
        self.assignmentID = assignmentID
        self.reviewerID = reviewerID
        self.revieweeID = revieweeID

    def __repr__(self):
        return f"<Review id={self.id} assignmentID={self.assignmentID}>"

    @classmethod
    def get_by_id(cls, review_id):
        """Get review by ID (relationships are eagerly loaded via lazy='joined')"""
        return db.session.get(cls, int(review_id))

    @classmethod
    def get_by_id_with_relations(cls, review_id):
        """Get review by ID with all relationships explicitly loaded."""
        return (
            cls.query.options(joinedload(cls.assignment).joinedload("course"))
            .filter_by(id=int(review_id))
            .first()
        )

    @classmethod
    def get_all_with_relations(cls):
        """Get all reviews with relationships loaded."""
        return cls.query.options(joinedload(cls.assignment).joinedload("course")).all()

    @classmethod
    def get_reviews_for_student(cls, assignment_id, student_id):
        """Get all reviews where a student is the reviewee for a given assignment."""
        return cls.query.filter_by(
            assignmentID=assignment_id, revieweeID=student_id
        ).all()

    @classmethod
    def get_reviews_by_assignment(cls, assignment_id):
        """Get all reviews for a given assignment."""
        return cls.query.filter_by(assignmentID=assignment_id).all()

    @classmethod
    def create_review(cls, review):
        """Add a new review to the database"""
        db.session.add(review)
        db.session.commit()
        return review

    @classmethod
    def review_exists(cls, reviewer_id, reviewee_id, assignment_id):
        """Check if a review already exists for this reviewer/reviewee/assignment combination."""
        return (
            cls.query.filter_by(
                reviewerID=reviewer_id,
                revieweeID=reviewee_id,
                assignmentID=assignment_id,
            ).first()
            is not None
        )

    def update(self):
        """Update review in the database"""
        db.session.commit()

    def delete(self):
        """Delete review from the database"""
        db.session.delete(self)
        db.session.commit()
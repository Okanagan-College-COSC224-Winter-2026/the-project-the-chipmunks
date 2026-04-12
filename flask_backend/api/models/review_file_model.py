"""
ReviewFile model for the peer evaluation app.
Stores file attachments uploaded alongside peer reviews.
"""
from datetime import datetime
from .db import db

class ReviewFile(db.Model):
    """File attachment linked to a specific peer review."""
    __tablename__ = "ReviewFile"
    id = db.Column(db.Integer, primary_key=True)
    reviewID = db.Column(db.Integer, db.ForeignKey("Review.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    uploaderID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    # relationships
    review = db.relationship("Review", back_populates="files", lazy="joined")
    uploader = db.relationship("User", lazy="joined")

    def __init__(self, reviewID, filename, file_path, uploaderID):
        self.reviewID = reviewID
        self.filename = filename
        self.file_path = file_path
        self.uploaderID = uploaderID

    def __repr__(self):
        return f"<ReviewFile id={self.id} reviewID={self.reviewID} filename={self.filename}>"

    @classmethod
    def get_by_id(cls, file_id):
        return db.session.get(cls, int(file_id))

    @classmethod
    def get_by_review(cls, review_id):
        return cls.query.filter_by(reviewID=int(review_id)).all()

    @classmethod
    def create(cls, review_file):
        db.session.add(review_file)
        db.session.commit()
        return review_file

    def delete(self):
        db.session.delete(self)
        db.session.commit()
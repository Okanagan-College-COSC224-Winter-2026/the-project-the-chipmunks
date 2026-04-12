"""
Announcement model for the peer evaluation app.
"""

from datetime import datetime, timezone

from .db import db


class Announcement(db.Model):
    """Course announcement posted by a teacher or admin."""

    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("Course.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    course = db.relationship("Course", backref=db.backref("announcements", lazy="dynamic"))
    author = db.relationship("User", backref=db.backref("announcements", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "content": self.content,
            "author_name": self.author.name if self.author else "Unknown",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Announcement id={self.id} course_id={self.course_id}>"

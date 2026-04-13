"""
Notification model for the peer evaluation app.
"""

from datetime import datetime, timezone

from .db import db


NOTIFICATION_TYPES = [
    "review_assigned",
    "review_received",
    "grade_posted",
    "feedback_received",
    "account_update",
    "announcement",
]


class Notification(db.Model):
    """Notification model for user alerts and activity feed"""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User", backref=db.backref("notifications", lazy="dynamic")
    )

    def __repr__(self):
        return f"<Notification id={self.id} type={self.type} user_id={self.user_id}>"

"""
Message model for the peer evaluation app.
"""

from datetime import datetime

from .db import db


class Message(db.Model):
    """Message model representing in-group student chat messages."""

    __tablename__ = "Message"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("CourseGroup.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    sender = db.relationship("User", backref=db.backref("sent_messages", lazy="dynamic"))
    group = db.relationship("CourseGroup", backref=db.backref("messages", lazy="dynamic"))

    def __init__(self, group_id, sender_id, content, is_read=False):
        self.group_id = group_id
        self.sender_id = sender_id
        self.content = content
        self.is_read = is_read

    def __repr__(self):
        return f"<Message id={self.id} group_id={self.group_id} sender_id={self.sender_id}>"
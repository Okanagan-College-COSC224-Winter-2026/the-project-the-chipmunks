"""
Message model for the peer evaluation app.
Stores in-group messages sent between students in the same assignment group.
"""
from datetime import datetime, timezone
from .db import db

class Message(db.Model):
    """Message model for in-group student communication."""
    __tablename__ = "Message"
    id = db.Column(db.Integer, primary_key=True)
    groupID = db.Column(
        db.Integer, db.ForeignKey("CourseGroup.id"), nullable=False, index=True
    )
    senderID = db.Column(
        db.Integer, db.ForeignKey("User.id"), nullable=False, index=True
    )
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    # relationships
    sender = db.relationship("User", foreign_keys=[senderID])
    group = db.relationship("CourseGroup", foreign_keys=[groupID])

    def __init__(self, groupID, senderID, content):
        self.groupID = groupID
        self.senderID = senderID
        self.content = content

    def __repr__(self):
        return f"<Message id={self.id} groupID={self.groupID} senderID={self.senderID}>"

    def to_dict(self):
        """Serialise to the shape the frontend expects."""
        return {
            "id":          self.id,
            "group_id":    self.groupID,
            "sender_id":   self.senderID,
            "sender_name": self.sender.name if self.sender else "Unknown",
            "content":     self.content,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "is_read":     self.is_read,
        }

    # ── Class methods ─────────────────────────────────────────────────────────

    @classmethod
    def get_by_group(cls, group_id):
        """Return all messages for a group ordered oldest-first."""
        return (
            cls.query
            .filter_by(groupID=group_id)
            .order_by(cls.created_at.asc())
            .all()
        )

    @classmethod
    def create(cls, message):
        db.session.add(message)
        db.session.commit()
        return message
"""
DirectMessage model for the peer evaluation app.
Stores private 1-on-1 messages between any two users.
"""
from datetime import datetime, timezone
from .db import db


class DirectMessage(db.Model):
    """Direct message between two users."""

    __tablename__ = "DirectMessage"

    id          = db.Column(db.Integer, primary_key=True)
    senderID    = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    recipientID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    content     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, nullable=False, default=False)
    created_at  = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    sender    = db.relationship("User", foreign_keys=[senderID])
    recipient = db.relationship("User", foreign_keys=[recipientID])

    def __init__(self, senderID, recipientID, content):
        self.senderID    = senderID
        self.recipientID = recipientID
        self.content     = content

    def to_dict(self):
        return {
            "id":             self.id,
            "sender_id":      self.senderID,
            "recipient_id":   self.recipientID,
            "sender_name":    self.sender.name    if self.sender    else "Unknown",
            "recipient_name": self.recipient.name if self.recipient else "Unknown",
            "content":        self.content,
            "is_read":        self.is_read,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_conversation(cls, user_a: int, user_b: int):
        """Return all messages between two users, oldest-first."""
        return (
            cls.query
            .filter(
                db.or_(
                    db.and_(cls.senderID == user_a, cls.recipientID == user_b),
                    db.and_(cls.senderID == user_b, cls.recipientID == user_a),
                )
            )
            .order_by(cls.created_at.asc())
            .all()
        )

    @classmethod
    def mark_read(cls, reader_id: int, sender_id: int):
        """Mark all unread messages from sender_id to reader_id as read."""
        cls.query.filter_by(
            senderID=sender_id,
            recipientID=reader_id,
            is_read=False,
        ).update({"is_read": True})
        db.session.commit()

    def __repr__(self):
        return f"<DirectMessage id={self.id} from={self.senderID} to={self.recipientID}>"

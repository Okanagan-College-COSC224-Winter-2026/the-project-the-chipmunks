from api.models.db import db
from api.models.notification_model import Notification


def create_notification(user_id, type, title, message, link=None):
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link,
    )
    db.session.add(notification)
    db.session.commit()
    return notification

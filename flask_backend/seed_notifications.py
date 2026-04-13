"""
seed_notifications.py — run this once before your demo to populate
all notification types for a user so every filter tab has content.

Usage (from the flask_backend/ directory):
    python seed_notifications.py

Or with a specific user email:
    python seed_notifications.py admin@example.com

It will print the user it seeded for and how many notifications were created.
"""

import sys
import os

# Make sure the app context is available
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app
from api.models.db import db
from api.models.notification_model import Notification
from api.models import User

app = create_app()

DEMO_NOTIFICATIONS = [
    {
        "type": "review_assigned",
        "title": "New Peer Review Assigned",
        "message": "You have been assigned to review Ayman Bouhafa in Hello.",
        "link": "/assignments/2",
    },
    {
        "type": "review_assigned",
        "title": "Peer Review Due Soon",
        "message": "Your review for Simon Velez in Example Assignment is due tomorrow.",
        "link": "/assignments/1",
    },
    {
        "type": "review_received",
        "title": "You Received a Peer Review",
        "message": "Simon Velez submitted a peer review for you in Hello.",
        "link": "/student/review-history",
    },
    {
        "type": "review_received",
        "title": "New Review on Example Assignment",
        "message": "Peer Reviewer A submitted a peer review for you in Example Assignment.",
        "link": "/student/review-history",
    },
    {
        "type": "grade_posted",
        "title": "Grade Posted",
        "message": "Your average score for Example Assignment has been calculated: 4.5 / 5.",
        "link": "/student/review-history",
    },
    {
        "type": "feedback_received",
        "title": "Feedback Available",
        "message": "Your instructor has posted conclusion files for Hello.",
        "link": "/assignments/2",
    },
    {
        "type": "account_update",
        "title": "Profile Updated",
        "message": "Your display name was successfully updated.",
        "link": "/profile/1",
    },
    {
        "type": "announcement",
        "title": "Course Announcement",
        "message": "COSC 404: The final peer review deadline has been extended to April 20.",
        "link": "/classes/1/home",
    },
    {
        "type": "announcement",
        "title": "Welcome to Toodle!",
        "message": "Your instructor has set up peer evaluations for this course. Check the assignments tab to get started.",
        "link": "/home",
    },
]


def seed_for_user(email: str):
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"  ✗  No user found with email: {email}")
        return 0

    created = 0
    for n in DEMO_NOTIFICATIONS:
        notif = Notification(
            user_id=user.id,
            type=n["type"],
            title=n["title"],
            message=n["message"],
            link=n.get("link"),
            is_read=False,
        )
        db.session.add(notif)
        created += 1

    db.session.commit()
    print(f"  ✓  Seeded {created} notifications for {user.name} ({user.email})")
    return created


if __name__ == "__main__":
    target_email = sys.argv[1] if len(sys.argv) > 1 else "student@example.com"

    with app.app_context():
        total = seed_for_user(target_email)
        if total:
            print(f"\n  All notification types covered:")
            for t in ["review_assigned", "review_received", "grade_posted",
                      "feedback_received", "account_update", "announcement"]:
                count = sum(1 for n in DEMO_NOTIFICATIONS if n["type"] == t)
                print(f"    • {t}: {count} notification(s)")

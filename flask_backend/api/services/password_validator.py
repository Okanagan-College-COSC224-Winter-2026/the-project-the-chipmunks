"""
Password validation helper for the peer evaluation app.
Enforces security criteria for user password changes.
"""

import re


def validate_password(password):
    """
    Validate a password against security criteria.

    Returns a list of failure messages. An empty list means the password is valid.

    Criteria:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - Special characters (!_?#$%^&) are supported
    """
    failures = []

    if len(password) < 8:
        failures.append("Must be at least 8 characters")

    if not re.search(r"[A-Z]", password):
        failures.append("Must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        failures.append("Must contain at least one lowercase letter")

    if not re.search(r"[0-9]", password):
        failures.append("Must contain at least one number")

    return failures

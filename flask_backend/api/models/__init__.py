from .announcement_model import Announcement
from .assignment_model import Assignment
from .conclusion_model import Conclusion
from .conclusion_file_model import ConclusionFile
from .course_group_model import CourseGroup
from .course_model import Course
from .criteria_description_model import CriteriaDescription
from .criterion_model import Criterion
from .db import db, ma
from .direct_message_model import DirectMessage
from .group_members_model import Group_Members
from .message_model import Message
from .notification_model import Notification
from .review_file_model import ReviewFile
from .review_model import Review
from .rubric_model import Rubric
from .submission_model import Submission
from .user_course_model import User_Course
from .user_model import User
from .schemas import (
    UserSchema,
    UserLoginSchema,
    UserRegistrationSchema,
    CourseSchema,
    CourseListSchema,
    CourseGroupSchema,
    AssignmentSchema,
    CriterionSchema,
    CriteriaDescriptionSchema,
    ReviewSchema,
    ReviewFileSchema,
    ConclusionFileSchema,
    RubricSchema,
    SubmissionSchema,
    UserCourseSchema,
    GroupMembersSchema,
)

__all__ = [
    # Models
    "Announcement",
    "DirectMessage",
    "User",
    "Course",
    "CourseGroup",
    "Assignment",
    "Criterion",
    "CriteriaDescription",
    "Review",
    "ReviewFile",
    "Conclusion",
    "ConclusionFile",
    "Rubric",
    "Submission",
    "User_Course",
    "Group_Members",
    "Notification",
    "Message",
    # Schemas
    "UserSchema",
    "UserLoginSchema",
    "UserRegistrationSchema",
    "CourseSchema",
    "CourseListSchema",
    "CourseGroupSchema",
    "AssignmentSchema",
    "CriterionSchema",
    "CriteriaDescriptionSchema",
    "ReviewSchema",
    "ReviewFileSchema",
    "ConclusionFileSchema",
    "RubricSchema",
    "SubmissionSchema",
    "UserCourseSchema",
    "GroupMembersSchema",
]
from marshmallow import Schema, fields


# ----------------------------
# User schemas (must match auth_controller.py)
# ----------------------------

class UserSchema(Schema):
    """Full user schema for serialization (excludes password)"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    role = fields.Str()
    must_change_password = fields.Bool()
    is_active = fields.Bool()


class UserLoginSchema(Schema):
    """Schema for login — auth_controller uses email + password"""
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class UserRegistrationSchema(Schema):
    """Schema for registration — auth_controller uses name + email + password"""
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class UserListSchema(Schema):
    """Lightweight user schema for lists"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    role = fields.Str()


# ----------------------------
# Course schemas
# ----------------------------

class CourseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    teacherID = fields.Int()
    teacher = fields.Nested(UserListSchema, dump_only=True)
    students = fields.List(fields.Nested(UserListSchema), dump_only=True)


class CourseListSchema(Schema):
    """Lightweight course schema for lists"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    teacherID = fields.Int()


class CourseGroupSchema(Schema):
    id = fields.Int(dump_only=True)
    courseID = fields.Int(required=True)
    name = fields.Str()
    assignmentID = fields.Int()


# ----------------------------
# Assignment
# ----------------------------

class AssignmentSchema(Schema):
    id = fields.Int(dump_only=True)
    courseID = fields.Int(required=True)
    name = fields.Str()
    rubric = fields.Str(allow_none=True)
    description_html = fields.Str(allow_none=True)
    attachment_filename = fields.Str(allow_none=True)
    has_attachment = fields.Bool(dump_only=True)
    due_date = fields.DateTime(allow_none=True)


# ----------------------------
# Rubric / criteria
# ----------------------------

class CriterionSchema(Schema):
    id = fields.Int(dump_only=True)
    reviewID = fields.Int(required=True)
    criterionRowID = fields.Int(required=True)
    grade = fields.Int()
    comments = fields.Str(allow_none=True)


class CriteriaDescriptionSchema(Schema):
    id = fields.Int(dump_only=True)
    rubricID = fields.Int(required=True)
    question = fields.Str(required=True)
    scoreMax = fields.Int()
    hasScore = fields.Bool()
    canComment = fields.Bool()


class RubricSchema(Schema):
    id = fields.Int(dump_only=True)
    assignmentID = fields.Int(required=True)
    canComment = fields.Bool()


# ----------------------------
# Reviews + attached review files
# ----------------------------

class ReviewSchema(Schema):
    id = fields.Int(dump_only=True)
    reviewerID = fields.Int(required=True)
    revieweeID = fields.Int(required=True)
    assignmentID = fields.Int(required=True)
    reviewer = fields.Nested(UserListSchema, dump_only=True)
    reviewee = fields.Nested(UserListSchema, dump_only=True)
    assignment = fields.Nested(AssignmentSchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ReviewListSchema(Schema):
    """Lightweight review schema for list endpoints — no nested assignment"""
    id = fields.Int(dump_only=True)
    assignmentID = fields.Int()
    reviewer = fields.Nested(UserListSchema, dump_only=True)
    reviewee = fields.Nested(UserListSchema, dump_only=True)


class ReviewFileSchema(Schema):
    id = fields.Int(dump_only=True)
    reviewID = fields.Int(required=True)
    filename = fields.Str(required=True)
    file_path = fields.Str(required=True)
    uploaded_at = fields.DateTime(dump_only=True)
    uploaderID = fields.Int(required=True)


# ----------------------------
# Submissions
# ----------------------------

class SubmissionSchema(Schema):
    id = fields.Int(dump_only=True)
    assignmentID = fields.Int(required=True)
    userID = fields.Int(required=True)
    submitted_at = fields.DateTime(dump_only=True)


class UserCourseSchema(Schema):
    id = fields.Int(dump_only=True)
    userID = fields.Int(required=True)
    courseID = fields.Int(required=True)


class GroupMembersSchema(Schema):
    id = fields.Int(dump_only=True)
    groupID = fields.Int(required=True)
    userID = fields.Int(required=True)
    assignmentID = fields.Int(required=True)


# ----------------------------
# Conclusion files (teacher uploads)
# ----------------------------

class ConclusionFileSchema(Schema):
    id = fields.Int(dump_only=True)
    assignmentID = fields.Int(required=True)
    teacherID = fields.Int(required=True)
    filename = fields.Str(required=True)
    file_path = fields.Str(required=True)
    uploaded_at = fields.DateTime(dump_only=True)


# ----------------------------
# Password change (Feature C)
# ----------------------------

class PasswordChangeSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True)
"""
Submission model for the peer evaluation app.
Stores assignment submissions (individual or group) uploaded by students.
"""

from datetime import datetime
from .db import db


class Submission(db.Model):
    """Submission model representing a file a student submits for an assignment."""

    __tablename__ = "Submission"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    studentID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    # group_id is set for group submissions so all members can see the file
    group_id = db.Column(db.Integer, db.ForeignKey("CourseGroup.id"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    # 'individual' or 'group'
    submission_mode = db.Column(db.String(20), nullable=False, default="individual")
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    student = db.relationship("User", back_populates="submissions")
    assignment = db.relationship("Assignment", back_populates="submissions")

    def __init__(self, assignmentID, studentID, filename, file_path,
                 submission_mode="individual", group_id=None):
        self.assignmentID = assignmentID
        self.studentID = studentID
        self.filename = filename
        self.file_path = file_path
        self.submission_mode = submission_mode
        self.group_id = group_id

    def __repr__(self):
        return (f"<Submission id={self.id} student={self.studentID} "
                f"assignment={self.assignmentID} mode={self.submission_mode}>")

    @classmethod
    def get_by_id(cls, submission_id):
        return db.session.get(cls, int(submission_id))

    @classmethod
    def get_by_student_assignment(cls, student_id, assignment_id):
        """Get all individual submissions by a student for an assignment."""
        return cls.query.filter_by(
            studentID=int(student_id),
            assignmentID=int(assignment_id),
            submission_mode="individual",
        ).all()

    @classmethod
    def get_by_group_assignment(cls, group_id, assignment_id):
        """Get all group submissions for a group and assignment."""
        return cls.query.filter_by(
            group_id=int(group_id),
            assignmentID=int(assignment_id),
            submission_mode="group",
        ).all()

    @classmethod
    def create(cls, submission):
        db.session.add(submission)
        db.session.commit()
        return submission

    def delete(self):
        db.session.delete(self)
        db.session.commit()

"""
ConclusionFile model for the peer evaluation app.
Stores conclusion/summary files uploaded by teachers for assignments.
"""
from datetime import datetime
from .db import db

class ConclusionFile(db.Model):
    """File attachment linked to an assignment conclusion (teacher-uploaded)."""
    __tablename__ = "ConclusionFile"
    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    teacherID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    # relationships
    assignment = db.relationship("Assignment", back_populates="conclusion_files", lazy="joined")
    teacher = db.relationship("User", lazy="joined")

    def __init__(self, assignmentID, filename, file_path, teacherID):
        self.assignmentID = assignmentID
        self.filename = filename
        self.file_path = file_path
        self.teacherID = teacherID

    def __repr__(self):
        return f"<ConclusionFile id={self.id} assignmentID={self.assignmentID}>"

    @classmethod
    def get_by_id(cls, file_id):
        return db.session.get(cls, int(file_id))

    @classmethod
    def get_by_assignment(cls, assignment_id):
        return cls.query.filter_by(assignmentID=int(assignment_id)).all()

    @classmethod
    def create(cls, conclusion_file):
        db.session.add(conclusion_file)
        db.session.commit()
        return conclusion_file

    def delete(self):
        db.session.delete(self)
        db.session.commit()
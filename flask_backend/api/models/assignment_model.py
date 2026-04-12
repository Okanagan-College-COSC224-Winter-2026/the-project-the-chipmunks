"""
Assignment model for the peer evaluation app.
"""
from datetime import datetime, timezone, timedelta
from .db import db

class Assignment(db.Model):
    """Assignment model representing assignments in a course"""
    __tablename__ = "Assignment"
    id = db.Column(db.Integer, primary_key=True)
    courseID = db.Column(db.Integer, db.ForeignKey("Course.id"), index=True)
    name = db.Column(db.String(255), nullable=True)
    # existing column name in DB is "rubric" but we use rubric_text in code
    rubric_text = db.Column("rubric", db.String(255), nullable=True)
    # NEW (Enhanced Assignment Management)
    description_html = db.Column(db.Text, nullable=True)
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_path = db.Column(db.String(512), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True, index=True)
    # relationships
    course = db.relationship("Course", back_populates="assignments", lazy="joined")
    rubrics = db.relationship(
        "Rubric", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )
    reviews = db.relationship(
        "Review", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )
    submissions = db.relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )
    group_members = db.relationship(
        "Group_Members", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )
    groups = db.relationship(
        "CourseGroup", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )
    conclusion_files = db.relationship(
        "ConclusionFile", back_populates="assignment", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(
        self,
        courseID,
        name,
        rubric_text=None,
        due_date=None,
        description_html=None,
        attachment_filename=None,
        attachment_path=None,
    ):
        self.courseID = courseID
        self.name = name
        self.rubric_text = rubric_text
        self.due_date = due_date
        self.description_html = description_html
        self.attachment_filename = attachment_filename
        self.attachment_path = attachment_path

    def __repr__(self):
        return f"<Assignment id={self.id} courseID={self.courseID} name={self.name}>"

    def can_modify(self) -> bool:
        """
        Return True if assignment can still be edited/deleted (i.e., due_date not passed).
        Key detail (fixes flaky tests):
        - If due_date is naive (SQLite/tests), compare against naive datetime.now().
        - If due_date is timezone-aware, compare in UTC.
        - Add a small grace window to avoid "due_date == now" race conditions.
        """
        if self.due_date is None:
            return True
        grace = timedelta(seconds=2)
        due = self.due_date
        # Naive datetime: compare naive-to-naive (most tests / SQLite)
        if due.tzinfo is None:
            return datetime.now() <= (due + grace)
        # Aware datetime: compare in UTC
        now_utc = datetime.now(timezone.utc)
        due_utc = due.astimezone(timezone.utc)
        return now_utc <= (due_utc + grace)

    @classmethod
    def get_by_id(cls, assignment_id):
        return db.session.get(cls, int(assignment_id))

    @classmethod
    def get_by_class_id(cls, class_id):
        return cls.query.filter_by(courseID=int(class_id)).all()

    @classmethod
    def create(cls, assignment):
        db.session.add(assignment)
        db.session.commit()
        return assignment

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

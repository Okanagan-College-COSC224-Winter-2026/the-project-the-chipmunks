import os

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from ..models import User, Course, Assignment
from ..models.db import db
from ..models.user_course_model import User_Course
from ..models.review_model import Review
from ..models.rubric_model import Rubric
from ..models.criteria_description_model import CriteriaDescription
from ..models.criterion_model import Criterion


@click.command("init_db")
@with_appcontext
def init_db_command():
    """Initialize the database"""
    db.create_all()
    click.echo("Database is created")


@click.command("drop_db")
@with_appcontext
def drop_db_command():
    """Drop all database tables"""
    if click.confirm("Are you sure you want to drop all tables?"):
        db.drop_all()
        click.echo("Database tables dropped")


@click.command("add_users")
@with_appcontext
def add_users_command():
    """Add sample users to the database"""
    sample_users = [
        {
            "name": "Example Student",
            "email": "student@example.com",
            "password": "123456",
            "role": "student",
        },
        {
            "name": "Example Teacher",
            "email": "teacher@example.com",
            "password": "123456",
            "role": "teacher",
        },
        {
            "name": "Example Admin",
            "email": "admin@example.com",
            "password": "123456",
            "role": "admin",
        },
    ]

    for u in sample_users:
        if not User.get_by_email(u["email"]):
            hashed = generate_password_hash(u["password"], method="pbkdf2:sha256")
            user = User(name=u["name"], email=u["email"], hash_pass=hashed, role=u["role"])
            User.create_user(user)
            click.echo(f"User '{user.email}' created (role={user.role})")
        else:
            click.echo(f"User '{u['email']}' already exists")


@click.command("create_admin")
@with_appcontext
def create_admin_command():
    """Create an admin user"""
    name = click.prompt("Admin name")
    email = click.prompt("Admin email")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    if User.get_by_email(email):
        click.echo(f"Error: User with email '{email}' already exists", err=True)
        return

    hashed = generate_password_hash(password, method="pbkdf2:sha256")
    admin = User(name=name, email=email, hash_pass=hashed, role="admin")
    User.create_user(admin)
    click.echo(f"Admin user '{email}' created successfully")


@click.command("ensure_admin")
@with_appcontext
def ensure_admin_command():
    """Ensure a default admin exists using environment variables.

    Requires DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD.
    Safe to run repeatedly; updates role/password if the user already exists.
    """

    name = os.environ.get("DEFAULT_ADMIN_NAME")
    email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

    if not all([name, email, password]):
        click.echo(
            "DEFAULT_ADMIN_* environment variables not fully set; skipping admin bootstrap"
        )
        return

    assert name is not None
    assert email is not None
    assert password is not None

    existing_user = User.get_by_email(email)
    hashed = generate_password_hash(password, method="pbkdf2:sha256")

    if existing_user:
        if existing_user.role != "admin" or existing_user.hash_pass != hashed:
            existing_user.role = "admin"
            existing_user.hash_pass = hashed
            existing_user.update()
            click.echo(f"Updated existing user '{email}' to admin role")
        else:
            click.echo(f"Admin user '{email}' already exists; no changes made")
        return

    admin = User(name=name, email=email, hash_pass=hashed, role="admin")
    User.create_user(admin)
    click.echo(f"Admin user '{email}' created successfully")


@click.command("add_sample_courses")
@with_appcontext
def add_sample_courses_command():
    """Add sample courses and assignments to the database"""
    teacher = User.get_by_email("teacher@example.com")
    if not teacher:
        click.echo("Error: Teacher user 'teacher@example.com' not found. Run 'flask add_users' first.", err=True)
        return

    sample_courses = [
        {"name": "COSC 404 Advanced Database Management Systems"},
        {"name": "COSC 470 Software Engineering"},
        {"name": "COSC 360 Server Platform As A Service"},
    ]

    for course_data in sample_courses:
        existing_course = Course.get_by_name_teacher(course_data["name"], teacher.id)
        if existing_course:
            click.echo(f"Course '{course_data['name']}' already exists")
            continue

        course = Course(teacherID=teacher.id, name=course_data["name"])
        Course.create_course(course)
        click.echo(f"Course '{course.name}' created (id={course.id})")

        assignment = Assignment(
            courseID=course.id,
            name="Example Assignment",
            rubric_text="Example rubric",
        )
        Assignment.create(assignment)
        click.echo(f"  - Assignment 'Example Assignment' added to '{course.name}'")

    click.echo("Sample courses and assignments created successfully")


@click.command("add_sample_reviews")
@with_appcontext
def add_sample_reviews_command():
    """Add sample peer reviews with grades for testing US20 grade display.

    Creates reviewers, enrolls the sample student in courses,
    and adds reviews with criterion scores so grades show up
    on the student dashboard.

    Prerequisites: Run 'flask add_users' and 'flask add_sample_courses' first.
    """
    # Get the sample student
    student = User.get_by_email("student@example.com")
    if not student:
        click.echo("Error: 'student@example.com' not found. Run 'flask add_users' first.", err=True)
        return

    teacher = User.get_by_email("teacher@example.com")
    if not teacher:
        click.echo("Error: 'teacher@example.com' not found. Run 'flask add_users' first.", err=True)
        return

    courses = Course.query.filter_by(teacherID=teacher.id).all()
    if not courses:
        click.echo("Error: No courses found. Run 'flask add_sample_courses' first.", err=True)
        return

    # Create two peer reviewers
    reviewers = []
    for name, email in [
        ("Peer Reviewer A", "reviewer_a@example.com"),
        ("Peer Reviewer B", "reviewer_b@example.com"),
    ]:
        existing = User.get_by_email(email)
        if existing:
            reviewers.append(existing)
            click.echo(f"Reviewer '{email}' already exists")
        else:
            hashed = generate_password_hash("123456", method="pbkdf2:sha256")
            reviewer = User(name=name, email=email, hash_pass=hashed, role="student")
            User.create_user(reviewer)
            reviewers.append(reviewer)
            click.echo(f"Reviewer '{email}' created")

    # Review data per course: different scores to show varied grades
    review_data = [
        {
            # Course 1: good grades (avg ~4.5/5 = green badge)
            "scores_by_reviewer": [
                [4, 5, 4],
                [5, 4, 5],
            ],
            "score_max": 5,
            "criteria_questions": [
                "Quality of work",
                "Communication skills",
                "Team contribution",
            ],
        },
        {
            # Course 2: okay grades (avg ~3.5/5 = yellow badge)
            "scores_by_reviewer": [
                [3, 4],
                [4, 3],
            ],
            "score_max": 5,
            "criteria_questions": [
                "Code quality",
                "Documentation",
            ],
        },
        {
            # Course 3: no reviews (shows "No grades yet" empty state)
            "scores_by_reviewer": [],
            "score_max": 5,
            "criteria_questions": [],
        },
    ]

    for idx, course in enumerate(courses):
        click.echo(f"\n--- {course.name} ---")

        # Enroll student in course
        existing_enrollment = User_Course.query.filter_by(
            userID=student.id, courseID=course.id
        ).first()
        if not existing_enrollment:
            User_Course.add(student.id, course.id)
            click.echo(f"  Enrolled student in course")
        else:
            click.echo(f"  Student already enrolled")

        # Enroll reviewers
        for reviewer in reviewers:
            if not User_Course.query.filter_by(userID=reviewer.id, courseID=course.id).first():
                User_Course.add(reviewer.id, course.id)

        data = review_data[idx] if idx < len(review_data) else review_data[-1]

        if not data["scores_by_reviewer"]:
            click.echo("  No reviews (empty grade state)")
            continue

        # Get or create assignment
        assignments = Assignment.query.filter_by(courseID=course.id).all()
        if not assignments:
            assignment = Assignment(courseID=course.id, name="Peer Review Assignment", rubric_text="Rubric")
            Assignment.create(assignment)
        else:
            assignment = assignments[0]
        click.echo(f"  Assignment: '{assignment.name}'")

        # Skip if reviews already exist
        if Review.query.filter_by(assignmentID=assignment.id, revieweeID=student.id).first():
            click.echo("  Reviews already exist, skipping")
            continue

        # Create rubric + criteria
        rubric = Rubric(assignmentID=assignment.id, canComment=True)
        db.session.add(rubric)
        db.session.commit()

        criteria_descs = []
        for question in data["criteria_questions"]:
            cd = CriteriaDescription(
                rubricID=rubric.id, question=question,
                scoreMax=data["score_max"], hasScore=True,
            )
            db.session.add(cd)
            db.session.commit()
            criteria_descs.append(cd)
            click.echo(f"    Criterion: '{question}' (max={data['score_max']})")

        # Create reviews with scores
        for r_idx, scores in enumerate(data["scores_by_reviewer"]):
            reviewer = reviewers[r_idx] if r_idx < len(reviewers) else reviewers[0]
            review = Review(
                assignmentID=assignment.id,
                reviewerID=reviewer.id,
                revieweeID=student.id,
            )
            db.session.add(review)
            db.session.commit()

            for s_idx, score in enumerate(scores):
                cd = criteria_descs[s_idx] if s_idx < len(criteria_descs) else criteria_descs[0]
                criterion = Criterion(
                    reviewID=review.id, criterionRowID=cd.id,
                    grade=score, comments=f"Feedback from {reviewer.name}",
                )
                db.session.add(criterion)
            db.session.commit()
            click.echo(f"  Review by '{reviewer.name}': scores={scores}")

    click.echo("\nDone! Log in as student@example.com (password: 123456) to see grades.")


def init_app(app):
    """Register CLI commands with the Flask app"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)
    app.cli.add_command(add_users_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(ensure_admin_command)
    app.cli.add_command(add_sample_courses_command)
    app.cli.add_command(add_sample_reviews_command)



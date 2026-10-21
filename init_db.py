from app import app
from models import db, Subject, Professor

with app.app_context():

    # Create tables if they do not already exist
    db.create_all()

    # Add default subjects
    subjects = [
        Subject(
            subject_code="OS",
            subject_name="Operating System",
            subject_type="Theory"
        ),
        Subject(
            subject_code="CT",
            subject_name="Computational Theory",
            subject_type="Theory"
        ),
        Subject(
            subject_code="DT",
            subject_name="Design Thinking",
            subject_type="Theory"
        ),
        Subject(
            subject_code="IOT",
            subject_name="Internet of Things",
            subject_type="Theory"
        ),
        Subject(
            subject_code="DBMS",
            subject_name="Database Management System",
            subject_type="Theory"
        )
    ]

    for subject in subjects:
        existing = Subject.query.filter_by(
            subject_code=subject.subject_code
        ).first()

        if not existing:
            db.session.add(subject)

    # Create the initial professor account only if it does not exist.
    # Configure secure credentials before using this in production.
    professor = Professor.query.filter_by(
        username="professor"
    ).first()

    if not professor:
        professor = Professor(
            username="professor",
            password="admin"
        )
        db.session.add(professor)

    db.session.commit()

    print("Database initialized successfully!")
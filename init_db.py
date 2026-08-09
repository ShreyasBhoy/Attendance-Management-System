from app import app
from models import db, Subject, Professor

with app.app_context():

    # Create tables
    db.create_all()

    # Add subjects
    subjects = [
        Subject(subjectcode="OS", subjectname="Operating System"),
        Subject(subjectcode="CT", subjectname="Computational Theory"),
        Subject(subjectcode="DT", subjectname="Design Thinking"),
        Subject(subjectcode="IOT", subjectname="Internet of Things"),
        Subject(subjectcode="DBMS", subjectname="Database Management System")
    ]

    for s in subjects:
        existing = Subject.query.filter_by(subjectcode=s.subjectcode).first()
        if not existing:
            db.session.add(s)

    # Add professor login
    prof = Professor.query.filter_by(username="professor").first()

    if not prof:
        prof = Professor(username="professor", password="admin")
        db.session.add(prof)

    db.session.commit()

    print("Database initialized successfully!")
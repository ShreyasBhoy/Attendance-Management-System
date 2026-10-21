from app import app
from models import db, Subject, Professor, ProfSubject

SUBJECTS = [
    ("DT-T", "Design Thinking", "Theory"),
    ("DBMS-T", "DBMS", "Theory"),
    ("OS-T", "Operating System", "Theory"),
    ("CT-T", "Computational Theory", "Theory"),
    ("IOT-T", "Internet of Things", "Theory"),
    ("MP-T", "Mini Project", "Theory"),
    ("DBMS-L", "DBMS Lab", "Lab"),
    ("OS-L", "OS Lab", "Lab"),
    ("IOT-L", "IOT Lab", "Lab"),
]

PROFESSORS = [
    "omkar",
    "swati",
    "anuja",
    "varsha",
    "rashmi",
    "rajashri",
    "kajal",
]

ASSIGNMENTS = [
    ("omkar", "DT-T"),
    ("swati", "DBMS-T"),
    ("anuja", "OS-T"),
    ("varsha", "CT-T"),
    ("rashmi", "IOT-T"),
    ("rajashri", "MP-T"),
    ("swati", "DBMS-L"),
    ("kajal", "OS-L"),
    ("rashmi", "IOT-L"),
]

with app.app_context():
    # Create database tables
    db.create_all()

    # Add subjects if missing
    for code, name, subject_type in SUBJECTS:
        if not Subject.query.filter_by(subject_code=code).first():
            db.session.add(
                Subject(
                    subject_code=code,
                    subject_name=name,
                    subject_type=subject_type,
                )
            )

    # Add professors if missing
    for username in PROFESSORS:
        if not Professor.query.filter_by(username=username).first():
            db.session.add(
                Professor(
                    username=username,
                    password="123",
                )
            )

    # Add professor-subject assignments if missing
    for professor, subject_code in ASSIGNMENTS:
        existing = ProfSubject.query.filter_by(
            professor=professor,
            subject_code=subject_code,
        ).first()

        if not existing:
            db.session.add(
                ProfSubject(
                    professor=professor,
                    subject_code=subject_code,
                )
            )

    db.session.commit()

    print("Database initialized successfully!")
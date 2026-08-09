from app import app, db
from sqlalchemy import inspect

expected_tables = [
    "student",
    "subject",
    "attendance",
    "professor",
    "prof_subject",
    "timetable",
    "marks"
]

with app.app_context():
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    print("Existing tables in DB:", existing_tables)

    for table in expected_tables:
        if table in existing_tables:
            print(f"✅ '{table}' exists")
        else:
            print(f"❌ '{table}' is missing")
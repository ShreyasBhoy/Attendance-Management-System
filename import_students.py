import pandas as pd
from app import app
from models import db, Student

with app.app_context():

    df = pd.read_excel("students.xlsx")

    for index, row in df.iterrows():

        student = Student(
            studentid=str(row["StudentID"]),
            name=row["Name"],
            division=row["Division"],
            email=row["Email"],
            password=str(row["Password"])
        )

        db.session.add(student)

    db.session.commit()

    print("Students Imported Successfully")
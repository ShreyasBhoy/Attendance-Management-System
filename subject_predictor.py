import pickle
import pandas as pd
import datetime
from models import Student, Attendance, Marks

# ---------------- CONFIG ----------------
REQUIRED_PERCENT = 75
SEM_END = datetime.date(2026, 5, 15)

# ---------------- LOAD MODEL ----------------
model = pickle.load(open("model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))

# ---------------- TIMETABLE (CAN MOVE TO DB LATER) ----------------
def get_subject_weekly_lectures(subject_code):
    timetable = {
        "OS-T": 3,
        "DBMS-T": 3,
        "IOT-T": 3,
        "CT-T": 3,
        "DT-T": 3,
        "MP-T": 3,

        "OS-L": 1,
        "DBMS-L": 1,
        "IOT-L": 1
    }
    return timetable.get(subject_code, 3)


# ---------------- CALCULATE REMAINING LECTURES ----------------
def get_remaining_days():
    today = datetime.date.today()
    return max((SEM_END - today).days, 0)


def calculate_remaining_lectures(subject_code):
    remaining_days = get_remaining_days()

    # remove weekends
    working_days = 0
    today = datetime.date.today()

    for i in range(remaining_days):
        day = today + datetime.timedelta(days=i)
        if day.weekday() < 5:  # Mon-Fri
            working_days += 1

    lectures_per_week = get_subject_weekly_lectures(subject_code)

    # approx conversion (5 working days = 1 week)
    remaining_weeks = working_days / 5

    return int(remaining_weeks * lectures_per_week)


# ---------------- STUDENT PREDICTION ----------------
def predict_for_student(student_id):

    results = []

    subjects = set(
        a.subject_code for a in Attendance.query.filter_by(student_id=student_id).all()
    )

    for subject in subjects:

        records = Attendance.query.filter_by(
            student_id=student_id,
            subject_code=subject
        ).all()

        total = len(records)
        present = sum(1 for r in records if r.status == "Present")

        if total == 0:
            continue

        current_percent = (present / total) * 100

        # ✅ dynamic remaining
        remaining = calculate_remaining_lectures(subject)

        # total lectures = completed + future
        total_lectures = total + remaining

        required_present = int((REQUIRED_PERCENT / 100) * total_lectures)
        needed = max(0, required_present - present)

        achievable = "YES" if needed <= remaining else "NO"

        # -------- ML PART --------
        marks = Marks.query.filter_by(
            student_id=student_id,
            subject_code=subject
        ).first()

        internal = marks.internal if marks else 0
        external = marks.external if marks else 0
        submission = marks.submission if marks else 0

        features = pd.DataFrame([{
            "attendance_percent": current_percent / 100,
            "internal": internal,
            "external": external,
            "submission": submission
        }])

        scaled = scaler.transform(features)
        pred = model.predict(scaled)[0]

        status = "Safe" if pred == 1 else "At Risk"

        results.append({
            "subject": subject,
            "current_percent": round(current_percent, 2),
            "needed": needed,
            "remaining": remaining,
            "status": status,
            "achievable": achievable
        })

    return results


# ---------------- PROFESSOR PREDICTION ----------------
def predict_for_professor(subject_code):

    results = []

    students = Student.query.all()

    for student in students:

        records = Attendance.query.filter_by(
            student_id=student.student_id,
            subject_code=subject_code
        ).all()

        total = len(records)
        present = sum(1 for r in records if r.status == "Present")

        if total == 0:
            continue

        current_percent = (present / total) * 100

        remaining = calculate_remaining_lectures(subject_code)
        total_lectures = total + remaining

        required_present = int((REQUIRED_PERCENT / 100) * total_lectures)
        needed = max(0, required_present - present)

        achievable = needed <= remaining

        # -------- ML PART --------
        marks = Marks.query.filter_by(
            student_id=student.student_id,
            subject_code=subject_code
        ).first()

        internal = marks.internal if marks else 0
        external = marks.external if marks else 0
        submission = marks.submission if marks else 0

        features = pd.DataFrame([{
            "attendance_percent": current_percent / 100,
            "internal": internal,
            "external": external,
            "submission": submission
        }])

        scaled = scaler.transform(features)
        pred = model.predict(scaled)[0]

        prediction = "PASS" if pred == 1 else "AT RISK"

        results.append({
            "id": student.student_id,
            "name": student.name,
            "attendance": round(current_percent, 2),
            "needed": needed,
            "remaining": remaining,
            "prediction": prediction,
            "achievable": achievable
        })

    return results


# ---------------- ADMIN (ALL SUBJECTS) ----------------
def predict_subject_wise():

    results = []

    students = Student.query.all()

    for student in students:

        student_data = predict_for_student(student.student_id)

        for d in student_data:
            results.append({
                "id": student.student_id,
                "name": student.name,
                **d
            })

    return results
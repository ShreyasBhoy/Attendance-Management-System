import datetime
from models import Attendance, Student
from app import app

REQUIRED_PERCENT = 0.75

SEM_END = datetime.date(2026, 5, 15)   # from calendar
LECTURES_PER_DAY = 5                   # from timetable


def calculate_remaining_lectures():
    today = datetime.date.today()
    remaining_days = (SEM_END - today).days

    # Remove weekends (simple version)
    working_days = 0
    for i in range(remaining_days):
        day = today + datetime.timedelta(days=i)
        if day.weekday() < 5:  # Mon-Fri
            working_days += 1

    return working_days * LECTURES_PER_DAY


def predict_for_student(student_id):
    with app.app_context():
        total = Attendance.query.filter_by(
            student_id=student_id
        ).count()

        present = Attendance.query.filter_by(
            student_id=student_id,
            status="Present"
        ).count()
    
    if total == 0:
        return None
     
    remaining = calculate_remaining_lectures()

    required_present = REQUIRED_PERCENT * (total + remaining)
    lectures_needed = required_present - present
    
    print("Total:", total)
    print("Present:", present)
    print("Remaining:", remaining)
     
    return {
        "current_percent": round((present/total)*100,2),
        "remaining_lectures": remaining,
        "lectures_needed": max(0, int(lectures_needed)),
        "status": "Achievable" if lectures_needed <= remaining else "Not Possible"
    }
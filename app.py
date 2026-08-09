from flask import Flask, render_template, request, redirect, url_for, session, send_file
from config import Config
from models import db, Student, Subject, Attendance, Professor, ProfSubject, Timetable, Marks
import pandas as pd
from datetime import date, timedelta
import pickle
import numpy as np

model = pickle.load(open("model.pkl","rb"))
scaler = pickle.load(open("scaler.pkl","rb"))

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "attendance_secret"

db.init_app(app)

# -------------------- LOGIN PAGE --------------------
@app.route("/")
def login():
    return render_template("login.html")


# -------------------- STUDENT LOGIN --------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    # LOGIN (POST)
    if request.method == "POST":
        userid = request.form.get("userid")
        password = request.form.get("password")

        student = Student.query.filter_by(student_id=userid).first()

        if not student or student.password != password:
            return "Invalid Student Login"

        session["role"] = "student"
        session["student_id"] = userid

    # BACK BUTTON / RELOAD (GET)
    if "student_id" not in session:
        return redirect("/student_login")

    userid = session["student_id"]
    student = Student.query.filter_by(student_id=userid).first()

    subjects = Subject.query.all()
    attendance_data = []

    for sub in subjects:

        total = Attendance.query.filter_by(
            student_id=userid,
            subject_code=sub.subject_code
        ).count()

        present = Attendance.query.filter_by(
            student_id=userid,
            subject_code=sub.subject_code,
            status="Present"
        ).count()

        percentage = 0 if total == 0 else round((present / total) * 100, 2)

        attendance_data.append({
            "name": sub.subject_name,
            "percent": percentage,
            "present": present,
            "total": total
        })

    total_classes = sum([row["total"] for row in attendance_data])
    total_present = sum([row["present"] for row in attendance_data])

    overall_percentage = 0 if total_classes == 0 else round(
        (total_present / total_classes) * 100, 2
    )

    # count low subjects
    low_count = len([s for s in attendance_data if s["percent"] < 75])

    marks = Marks.query.filter_by(student_id=userid).all()

    if marks:
        total = sum(m.internal + m.external + m.submission for m in marks)
        avg_marks = round(total / len(marks), 2)
    else:
        avg_marks = 0

    return render_template(
        "student_dashboard.html",
        name=student.name,
        subjects=attendance_data,
        overall=overall_percentage,
        low_count=low_count,
        avg_marks=avg_marks
    )
    
    


# -------------------- PROFESSOR LOGIN --------------------
@app.route("/prof_login", methods=["POST"])
def prof_login():

    username = request.form["username"]
    password = request.form["password"]

    prof = Professor.query.filter_by(username=username).first()

    if prof and prof.password == password:

        session["role"] = "professor"
        session["prof_name"] = prof.username

        # fetch subject assigned to professor
        ps = ProfSubject.query.filter_by(professor=prof.username).first()

        if ps:
            session["subject_code"] = ps.subject_code

        return redirect("/professor")

    return "Invalid Professor Login"

# -------------------- ADMIN LOGIN --------------------
@app.route("/admin_login", methods=["POST"])
def admin_login():

    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "admin123":
        session["role"] = "admin"
        return redirect("/admin")

    return "Invalid Admin Login"


# -------------------- PROFESSOR DASHBOARD --------------------
@app.route("/professor")
def professor_dashboard():

    if session.get("role") != "professor":
        return redirect("/")

    prof_name = session.get("prof_name")

    subjects = ProfSubject.query.filter_by(
        professor=prof_name
    ).all()

    return render_template(
        "professor_dashboard.html",
        name=prof_name,
        subjects=subjects
    )

# -------------------- ADMIN DASHBOARD --------------------
@app.route("/admin")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    from models import Student, Professor, Subject, Attendance

    total_students = Student.query.count()
    total_prof = Professor.query.count()
    total_subjects = Subject.query.count()
    total_records = Attendance.query.count()

    # ✅ REAL SUBJECT ATTENDANCE
    subjects_db = Subject.query.all()

    subjects = []

    for s in subjects_db:

        records = Attendance.query.filter_by(
            subject_code=s.subject_code
        ).all()

        total = len(records)
        present = len([r for r in records if r.status == "Present"])

        percent = round((present / total) * 100, 2) if total > 0 else 0

        subjects.append({
            "name": s.subject_name,   # ✅ FIXED (no more error)
            "attendance": percent
        })

    # ✅ REAL PASS / FAIL (BASED ON ATTENDANCE)
    pass_count = 0
    fail_count = 0

    students = Student.query.all()

    for student in students:

        records = Attendance.query.filter_by(
            student_id=student.student_id
        ).all()

        total = len(records)
        present = len([r for r in records if r.status == "Present"])

        if total == 0:
            continue

        percent = (present / total) * 100

        if percent >= 75:
            pass_count += 1
        else:
            fail_count += 1

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_prof=total_prof,
        total_subjects=total_subjects,
        total_records=total_records,
        subjects=subjects,
        pass_count=pass_count,
        fail_count=fail_count
    )

# -------------------- MARK ATTENDANCE --------------------
@app.route("/mark", methods=["GET"])
def mark():

    if session.get("role") != "professor":
        return redirect("/")

    username = session.get("prof_name")

    assigned = ProfSubject.query.filter_by(professor=username).all()
    subject_codes = [a.subject_code for a in assigned]

    subjects = Subject.query.filter(
        Subject.subject_code.in_(subject_codes)
    ).all()

    # get division from dropdown
    division = request.args.get("division")

    if division:
        students = Student.query.filter_by(division=division).all()
    else:
        students = Student.query.all()

    return render_template(
        "mark_attendance.html",
        students=students,
        subjects=subjects
    )

@app.route("/submit_attendance", methods=["POST"])
def submit_attendance():

    if session.get("role") != "professor":
        return redirect("/")

    subject = request.form["subject"]
    division = request.args.get("division")
    today = date.today() -timedelta(days=4)  # for testing purposes, we mark attendance for yesterday

    if division:
        students = Student.query.filter_by(division=division).all()
    else:
        students = Student.query.all()

    for s in students:

        status = "Present" if request.form.get(
            f"status_{s.student_id}"
        ) else "Absent"

        existing = Attendance.query.filter_by(
            student_id=s.student_id,
            subject_code=subject,
            date=today
        ).first()

        if not existing:
            attendance = Attendance(
                student_id=s.student_id,
                subject_code=subject,
                date=today,
                status=status
            )
            db.session.add(attendance)

    db.session.commit()

    return redirect("/professor")


# -------------------- VIEW ATTENDANCE --------------------
@app.route("/view")
def view_attendance():

    if session.get("role") != "professor":
        return redirect("/")

    username = session.get("prof_name")

    subjects = ProfSubject.query.filter_by(professor=username).all()
    subject_codes = [s.subject_code for s in subjects]

    records = Attendance.query.filter(
        Attendance.subject_code.in_(subject_codes)
    ).all()

    summary = {}

    for r in records:
        sid = r.student_id

        if sid not in summary:
            summary[sid] = {"total": 0, "present": 0}

        summary[sid]["total"] += 1
        if r.status == "Present":
            summary[sid]["present"] += 1

    percentage = {}

    for sid in summary:
        total = summary[sid]["total"]
        present = summary[sid]["present"]
        percentage[sid] = round((present / total) * 100, 2)

    return render_template(
        "view_attendance.html",
        records=records,
        percentage=percentage
    )


# -------------------- STUDENT ATTENDANCE --------------------
@app.route("/attendance_view")
def attendance_view():

    if session.get("role") != "student":
        return redirect("/")

    student_id = session.get("student_id")

    data = Attendance.query.filter_by(student_id=student_id).all()

    total = len(data)
    present = len([d for d in data if d.status == "Present"])

    percentage = 0
    if total > 0:
        percentage = (present / total) * 100

    return render_template(
        "attendance_view.html",
        data=data,
        percentage=round(percentage, 2)
    )


# -------------------- PERCENTAGE --------------------
@app.route("/percentage/<int:student_id>")
def percentage(student_id):

    student = Student.query.filter_by(student_id=student_id).first()
    subjects = Subject.query.all()

    data = []

    for sub in subjects:

        total = Attendance.query.filter_by(
            student_id=student_id,
            subject_code=sub.subject_code
        ).count()

        present = Attendance.query.filter_by(
            student_id=student_id,
            subject_code=sub.subject_code,
            status="Present"
        ).count()

        percent = 0 if total == 0 else round((present/total)*100,2)

        data.append({
            "subject": sub.subject_name,
            "percentage": percent
        })

    return render_template("percentage.html", student=student, data=data)


# -------------------- ADD STUDENT (ADMIN ONLY) --------------------
@app.route("/add_student", methods=["GET","POST"])
def add_student():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        student_id = request.form.get("student_id")
        name = request.form.get("name")
        division = request.form.get("division")

        new_student = Student(
            student_id=student_id,
            name=name,
            division=division
        )

        db.session.add(new_student)
        db.session.commit()

        return "Student Added Successfully"

    return render_template("add_student.html")

@app.route("/upload", methods=["GET","POST"])
def upload():

    if session.get("role") not in ["admin", "professor"]:
        return redirect("/")

    if request.method == "POST":

        file = request.files["file"]
        df = pd.read_excel(file)

        for index, row in df.iterrows():

            student = Student(
                student_id=row["StudentID"],
                name=row["Name"],
                division=row["Division"],
                class_name=row["Class"],
                email=row["Email"],
                password=row["Password"]
            )

            db.session.add(student)

        db.session.commit()

        return "Students Uploaded Successfully"

    return render_template("upload.html")



import pandas as pd
from flask import request, redirect, render_template, session

@app.route("/upload_marks", methods=["GET", "POST"])
def upload_marks():
    if session.get("role") not in ["admin", "professor"]:
        return redirect("/")

    # division filter
    division = request.args.get("division")
    students = Student.query.filter_by(division=division).all() if division else Student.query.all()

    # professor subjects
    username = session.get("prof_name")
    subjects = ProfSubject.query.filter_by(professor=username).all()
    prof_subject_codes = [s.subject_code.strip().upper() for s in subjects]

    if request.method == "POST":
        print("FILES:", request.files)

        # -------- Excel Upload --------
        if "file" in request.files:
            file = request.files["file"]

            if file and file.filename != "":
                import pandas as pd

                # Get subject from filename
                filename = file.filename.split('.')[0].lower()   # marks_iot-t
                subject_code_from_file = filename.replace("marks_", "").upper().strip()

                # check professor teaches subject
                if subject_code_from_file not in prof_subject_codes:
                    return f"Error: You don't teach {subject_code_from_file}"

                # read excel
                df = pd.read_excel(file, engine="openpyxl")
                df.columns = df.columns.str.strip()

                for _, row in df.iterrows():
                    try:

                        student_id = str(int(row["StudentID"])).strip() 

                        internal = int(row["Internal"]) if pd.notna(row["Internal"]) else 0
                        external = int(row["External"]) if pd.notna(row["External"]) else 0
                        submission = int(row["Submission"]) if pd.notna(row["Submission"]) else 0
                        
                        print("Saving:", row["StudentID"], subject_code_from_file, internal, external, submission)

                        m = Marks(
                            student_id=str(row["StudentID"]).strip(),
                            subject_code=subject_code_from_file,
                            internal=internal,
                            external=external,
                            submission=submission
                        )

                        db.session.add(m)

                    except Exception as e:
                        print("Row error:", e)
                
                db.session.commit()
                
                
                print("All Marks:", Marks.query.all())
                return f"Marks for {subject_code_from_file} uploaded successfully"

        # -------- Manual Entry --------
        student_id = request.form["student_id"]
        subject_code = request.form["subject_code"]

        internal = int(request.form.get("internal") or 0)
        external = int(request.form.get("external") or 0)
        submission = int(request.form.get("submission") or 0)

        m = Marks(
            student_id=str(student_id),
            subject_code=subject_code,
            internal=internal,
            external=external,
            submission=submission
        )

        db.session.add(m)
        db.session.commit()

        return redirect("/upload_marks")

    return render_template(
        "upload_marks.html",
        students=students,
        subjects=subjects
    )

@app.route("/result")
def result():

    if session.get("role") != "student":
        return redirect("/")

    sid = session.get("student_id")

    marks = Marks.query.filter_by(student_id=sid).all()

    return render_template("result.html", marks=marks)

# -------------------- EXPORT EXCEL --------------------
@app.route("/export")
def export():

    if session.get("role") != "professor":
        return redirect("/")

    records = Attendance.query.all()

    data = []

    for r in records:

        data.append({
            "Student ID": r.student_id,
            "Subject": r.subject_code,
            "Date": r.date,
            "Status": r.status
    })

    df = pd.DataFrame(data)

    file = "attendance.xlsx"
    df.to_excel(file, index=False)

    return send_file(file, as_attachment=True)



@app.route("/export_attendance")
def export_attendance():

    data = Attendance.query.all()

    rows = []

    for d in data:
        rows.append({
            "Student ID": d.student_id,
            "Subject": d.subject_code,
            "Date": d.date,
            "Status": d.status
        })

    df = pd.DataFrame(rows)

    file = "attendance.xlsx"
    df.to_excel(file, index=False)

    return send_file(file, as_attachment=True)




# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/multi_login", methods=["POST"])
def multi_login():

    userid = request.form["userid"]
    password = request.form["password"]
    role = request.form["role"]

    if role == "Student":
        return redirect(url_for("dashboard"), code=307)

    elif role == "Professor":

        prof = Professor.query.filter_by(username=userid).first()

        if prof and prof.password == password:
            session["role"] = "professor"
            session["prof_name"] = prof.username
            return redirect("/professor")

        return "Invalid Professor Login"

    elif role == "Admin":
        if userid == "admin" and password == "admin123":
            session["role"] = "admin"
            return redirect("/admin")

        return "Invalid Admin Login"
    

@app.route("/timetable")
def timetable():

    if session.get("role") != "professor":
        return redirect("/")

    username = session.get("prof_name")

    data = Timetable.query.filter_by(professor=username).all()

    return render_template("timetable.html", data=data)






@app.route("/add_professor", methods=["GET","POST"])
def add_professor():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        department = request.form["department"]

        prof = Professor(
            username=username,
            password=password,
            department=department
        )

        db.session.add(prof)
        db.session.commit()

        return redirect("/admin")

    return render_template("add_professor.html")


@app.route("/manage_subject", methods=["GET","POST"])
def manage_subject():

    if session.get("role") != "admin":
        return redirect("/")

    professors = Professor.query.all()
    subjects = Subject.query.all()

    if request.method == "POST":

        action = request.form["action"]

        # ADD SUBJECT
        if action == "add":
            code = request.form["code"]
            name = request.form["name"]
            type_ = request.form["type"]

            db.session.add(Subject(
                subject_code=code,
                subject_name=name,
                subject_type=type_
            ))

            db.session.commit()

        # ASSIGN SUBJECT
        elif action == "assign":
            professor = request.form["professor"]
            subject_code = request.form["subject_code"]

            db.session.add(ProfSubject(
                professor=professor,
                subject_code=subject_code
            ))

            db.session.commit()

        return redirect("/manage_subject")

    assignments = ProfSubject.query.all()

    return render_template(
        "manage_subject.html",
        professors=professors,
        subjects=subjects,
        assignments=assignments
    )


@app.route("/view_students")
def view_students():

    if session.get("role") != "admin":
        return redirect("/")

    division = request.args.get("division")

    if division:
        students = Student.query.filter_by(division=division).all()
    else:
        students = Student.query.all()

    return render_template(
        "view_students.html",
        students=students
    )

@app.route("/admin_timetable")
def admin_timetable():


    if session.get("role") != "admin":
        return redirect("/")

    timetable = Timetable.query.all()

    days = ["Mon","Tue","Wed","Thu","Fri"]
    times = [
        "9:30-10:30",
        "10:30-11:30",
        "11:30-12:30",
        "12:30-1:30",
        "1:30-2:30",
        "2-3"
    ]

    return render_template(
        "admin_timetable.html",
        timetable=timetable,
        days=days,
        times=times
    )


@app.route("/low_attendance")
def low_attendance():

    students = Student.query.all()
    low_students = []

    for student in students:

        total = Attendance.query.filter_by(
            student_id=student.student_id
        ).count()

        present = Attendance.query.filter_by(
            student_id=student.student_id,
            status="Present"
        ).count()

        if total > 0:
            percent = (present / total) * 100

            if percent < 75:
                low_students.append({
                    "id": student.student_id,
                    "name": student.name,
                    "division": student.division,
                    "percent": round(percent,2)
         })

    return render_template(
        "low_attendance.html",
        students=low_students
    )

@app.route("/ai_predict/<student_id>")
def ai_predict(student_id):

    marks = Marks.query.filter_by(student_id=student_id).all()
    attendance = Attendance.query.filter_by(student_id=student_id).all()

    if not marks or not attendance:
        return "Not enough data"

    # attendance %
    present = sum(1 for a in attendance if a.status.lower() == "present")
    attendance_percent = present / len(attendance)

    # marks avg
    internal = sum(m.internal for m in marks) / len(marks)
    external = sum(m.external for m in marks) / len(marks)
    submission = sum(m.submission for m in marks) / len(marks)

    features = np.array([[attendance_percent, internal, external, submission]])
    features = scaler.transform(features)

    prediction = model.predict(features)[0]

    result = "PASS" if prediction == 1 else "AT RISK"

    return f"AI Prediction: {result}"

@app.route("/ai_dashboard")
def ai_dashboard():

    from models import Student, Attendance, Marks
    import pickle
    import pandas as pd
    import numpy as np

    # ---------------- LOAD MODEL ----------------
    model = pickle.load(open("model.pkl", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb"))

    REQUIRED_PERCENT = 75

    # ---------------- REALISTIC REMAINING LECTURES ----------------
    def calculate_remaining_lectures():
        # realistic fixed remaining lectures for semester
        return 35   # ✔️ change if needed (15–25 is realistic)

    # ---------------- MAIN ----------------
    students_data = []
    students = Student.query.all()

    for student in students:

        # ===== ATTENDANCE =====
        attendance_records = Attendance.query.filter_by(
            student_id=student.student_id
        ).all()

        total_done = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status.lower() == "present")

        if total_done == 0:
            continue

        attendance_percent = (present / total_done) * 100

        # ✔️ realistic remaining
        remaining = calculate_remaining_lectures()

        total_final = total_done + remaining

        required_total_present = (REQUIRED_PERCENT / 100) * total_final

        needed = max(0, int(np.ceil(required_total_present - present)))

        achievable = needed <= remaining

        # ===== MARKS =====
        marks_records = Marks.query.filter_by(
            student_id=student.student_id
        ).all()

        if marks_records:
            internal = np.mean([m.internal or 0 for m in marks_records])
            external = np.mean([m.external or 0 for m in marks_records])
            submission = np.mean([m.submission or 0 for m in marks_records])
        else:
            internal = external = submission = 0

        avg_marks = round((internal + external + submission) / 3, 2)

        # ===== ML PREDICTION =====
        features = pd.DataFrame([{
            "attendance_percent": attendance_percent / 100,
            "internal": internal,
            "external": external,
            "submission": submission
        }])

        scaled = scaler.transform(features)
        pred = model.predict(scaled)[0]

        prediction = "PASS" if pred == 1 else "AT RISK"

        # ===== FINAL OUTPUT =====
        students_data.append({
            "id": student.student_id,
            "name": student.name,
            "attendance": round(attendance_percent, 2),
            "avg_marks": avg_marks,
            "needed": needed,
            "remaining": remaining,
            "prediction": prediction,
            "achievable": achievable
        })

    return render_template("ai_dashboard.html", students=students_data)

@app.route("/attendance_predictor")
def attendance_predictor():

    students = Student.query.all()
    results = []

    from attendance_predictor import predict_for_student

    for s in students:
        res = predict_for_student(s.student_id)
        if res:
            results.append({
                "id": s.student_id,
                "name": s.name,
                **res
            })

    return render_template("attendance_predictor.html", data=results)



@app.route("/student_subject_prediction")
def student_subject_prediction():

    from subject_predictor import predict_for_student   # ✅ IMPORT HERE

    student_id = session["student_id"]
    prediction = predict_for_student(student_id)

    return render_template(
        "student_subject_prediction.html",
        prediction=prediction
    )

@app.route("/prof_subject_ml/<subject_code>")
def prof_subject_ml(subject_code):

    if session.get("role") != "professor":
        return redirect("/")

    from subject_predictor import predict_for_professor
    data = predict_for_professor(subject_code)

    return render_template(
        "prof_subject_ml.html",
        data=data,
        subject=subject_code
    )

@app.route("/set_prof_subject/<subject_code>")
def set_prof_subject(subject_code):
    session["subject_code"] = subject_code
    return redirect("/prof_subject_ml")

@app.route("/admin_subject_ml")
def admin_subject_ml():

    data = predict_subject_wise()

    return render_template(
        "admin_subject_ml.html",
        data=data
    )


@app.route("/admin_reports")
def admin_reports():
    return "<h3>Reports Page</h3>"

@app.route("/test_students")
def test_students():
    students = Student.query.all()
    return str(len(students))

@app.route("/check_attendance")
def check_attendance():
    total = Attendance.query.count()
    present = Attendance.query.filter_by(status="Present").count()
    absent = Attendance.query.filter_by(status="Absent").count()

    return f"""
    Total Records: {total} <br>
    Present: {present} <br>
    Absent: {absent}
    """

# -------------------- RUN --------------------
if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        # Subjects
        if Subject.query.count() == 0:

            db.session.add(Subject(subject_code="DT-T", subject_name="Design Thinking", subject_type="Theory"))
            db.session.add(Subject(subject_code="DBMS-T", subject_name="DBMS", subject_type="Theory"))
            db.session.add(Subject(subject_code="OS-T", subject_name="Operating System", subject_type="Theory"))
            db.session.add(Subject(subject_code="CT-T", subject_name="Computational Theory", subject_type="Theory"))
            db.session.add(Subject(subject_code="IOT-T", subject_name="IOT", subject_type="Theory"))
            db.session.add(Subject(subject_code="MP-T", subject_name="Mini Project", subject_type="Theory"))

            db.session.add(Subject(subject_code="DBMS-L", subject_name="DBMS Lab", subject_type="Lab"))
            db.session.add(Subject(subject_code="OS-L", subject_name="OS Lab", subject_type="Lab"))
            db.session.add(Subject(subject_code="IOT-L", subject_name="IOT Lab", subject_type="Lab"))

            db.session.commit()

        # Professors
        if Professor.query.count() == 0:

            db.session.add(Professor(username="omkar", password="123"))
            db.session.add(Professor(username="swati", password="123"))
            db.session.add(Professor(username="anuja", password="123"))
            db.session.add(Professor(username="varsha", password="123"))
            db.session.add(Professor(username="rashmi", password="123"))
            db.session.add(Professor(username="rajashri", password="123"))
            db.session.add(Professor(username="kajal", password="123"))

            db.session.commit()

    

        if ProfSubject.query.count() == 0:

            db.session.add(ProfSubject(professor="omkar", subject_code="DT-T"))
            db.session.add(ProfSubject(professor="swati", subject_code="DBMS-T"))
            db.session.add(ProfSubject(professor="anuja", subject_code="OS-T"))
            db.session.add(ProfSubject(professor="varsha", subject_code="CT-T"))
            db.session.add(ProfSubject(professor="rashmi", subject_code="IOT-T"))
            db.session.add(ProfSubject(professor="rajashri", subject_code="MP-T"))

            db.session.add(ProfSubject(professor="swati", subject_code="DBMS-L"))
            db.session.add(ProfSubject(professor="kajal", subject_code="OS-L"))
            db.session.add(ProfSubject(professor="rashmi", subject_code="IOT-L"))

            db.session.commit()


        if Timetable.query.count() == 0:

        # Monday
            db.session.add(Timetable(professor="swati", subject_code="DBMS-T", class_name="SE-AIML", day="Mon", time="9:30-10:30"))
            db.session.add(Timetable(professor="anuja", subject_code="OS-T", class_name="SE-AIML", day="Mon", time="10:30-11:30"))
            db.session.add(Timetable(professor="varsha", subject_code="CT-T", class_name="SE-AIML", day="Mon", time="11:30-12:30"))
            db.session.add(Timetable(professor="rashmi", subject_code="IOT-T", class_name="SE-AIML", day="Mon", time="12:30-1:30"))
            db.session.add(Timetable(professor="rajashri", subject_code="MP-T", class_name="SE-AIML", day="Mon", time="2-3"))

        # Tuesday
            db.session.add(Timetable(professor="omkar", subject_code="DT-T", class_name="SE-AIML", day="Tue", time="12:30-1:30"))
            db.session.add(Timetable(professor="swati", subject_code="DBMS-T", class_name="SE-AIML", day="Tue", time="1:30-2:30"))
            db.session.add(Timetable(professor="rashmi", subject_code="IOT-T", class_name="SE-AIML", day="Tue", time="2-3"))

        # Wednesday
            db.session.add(Timetable(professor="swati", subject_code="DBMS-T", class_name="SE-AIML", day="Wed", time="9:30-10:30"))
            db.session.add(Timetable(professor="varsha", subject_code="CT-T", class_name="SE-AIML", day="Wed", time="11:30-12:30"))
            db.session.add(Timetable(professor="anuja", subject_code="OS-T", class_name="SE-AIML", day="Wed", time="12:30-1:30"))
            db.session.add(Timetable(professor="rashmi", subject_code="IOT-T", class_name="SE-AIML", day="Wed", time="2-3"))

        # Thursday
            db.session.add(Timetable(professor="varsha", subject_code="CT-T", class_name="SE-AIML", day="Thu", time="9:30-10:30"))
            db.session.add(Timetable(professor="anuja", subject_code="OS-T", class_name="SE-AIML", day="Thu", time="12:30-1:30"))
            db.session.add(Timetable(professor="rashmi", subject_code="IOT-T", class_name="SE-AIML", day="Thu", time="2-3"))

        # Friday
            db.session.add(Timetable(professor="anuja", subject_code="OS-T", class_name="SE-AIML", day="Fri", time="9:30-10:30"))
            db.session.add(Timetable(professor="varsha", subject_code="CT-T", class_name="SE-AIML", day="Fri", time="10:30-11:30"))
            db.session.add(Timetable(professor="swati", subject_code="DBMS-T", class_name="SE-AIML", day="Fri", time="11:30-12:30"))
            db.session.add(Timetable(professor="omkar", subject_code="DT-T", class_name="SE-AIML", day="Fri", time="12:30-1:30"))
            db.session.add(Timetable(professor="swati", subject_code="DBMS-T", class_name="SE-AIML", day="Fri", time="2-3"))

            db.session.commit()


        df = pd.read_excel("students.xlsx", engine="openpyxl")
        df.columns = df.columns.str.strip().str.lower()

        print("Columns:", df.columns)
        print("Total rows:", len(df))
        print(df.head())

        Student.query.delete()
        db.session.commit()
        for _, row in df.iterrows():
            student = Student(
                student_id=row["studentid"],
                name=row["name"],
                division=row["division"],
                class_name="SE-AIML",
                email=row["email"],
                password=row["password"]
            )
            db.session.add(student)

            db.session.commit()
            

    app.run(debug=True)
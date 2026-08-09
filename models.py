from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    student_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    division = db.Column(db.String(5))
    class_name = db.Column(db.String(20))
    email = db.Column(db.String(100))
    password = db.Column(db.String(50))
    


class Subject(db.Model):
    subject_code = db.Column(db.String(10), primary_key=True)
    subject_name = db.Column(db.String(100))
    subject_type = db.Column(db.String(10))  # Theory / Lab


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20))
    subject_code = db.Column(db.String(10))
    date = db.Column(db.Date)
    status = db.Column(db.String(10))


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))


class ProfSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professor = db.Column(db.String(50))
    subject_code = db.Column(db.String(10))


class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professor = db.Column(db.String(50))
    subject_code = db.Column(db.String(10))
    class_name = db.Column(db.String(20))
    day = db.Column(db.String(10))
    time = db.Column(db.String(20))


class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20))
    subject_code = db.Column(db.String(10))
    internal = db.Column(db.Integer)
    external = db.Column(db.Integer)
    submission = db.Column(db.Integer)
    
# Attendance-Management-System
# 📚 Student Attendance Management System

A web-based Student Attendance Management System built using Python Flask and PostgreSQL. The application helps educational institutions manage student records, track attendance, monitor attendance percentages, and predict whether students will meet the required attendance criteria using Machine Learning.

## 🚀 Live Demo

- **Live Website:** [Open Attendance Management System](https://attendance-management-system-j5bm.onrender.com)
- **GitHub Repository:** https://github.com/ShreyasBhoy/Attendance-Management-System

## 📌 Project Overview

Managing student attendance manually can be time-consuming and error-prone. This project provides a centralized web application where students, professors, and administrators can access relevant information through role-based login.

The system allows professors to mark attendance, students to monitor their attendance records, and administrators to manage academic information. It also incorporates Machine Learning to support attendance prediction.

## ✨ Features

### 👨‍🎓 Student Dashboard
- Student login and personalized dashboard.
- View subject-wise attendance records.
- Monitor attendance percentages.
- Identify subjects with attendance below 75%.
- Access available academic information.

### 👨‍🏫 Professor Dashboard
- Professor login.
- View assigned subjects.
- View student records.
- Mark and submit student attendance.
- Track attendance information.

### 🛡️ Admin Dashboard
- Administrative login.
- View student, professor, and subject counts.
- Monitor attendance records.
- Manage academic information supported by the application.

### 🤖 Machine Learning
- Attendance prediction using a trained ML model.
- Attendance-related analysis.
- Support for estimating whether students can meet the required attendance percentage.

### 🗓️ Academic Management
- Subject and timetable information.
- Attendance tracking by subject.
- Attendance percentage calculations.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| Flask-SQLAlchemy | Database integration |
| PostgreSQL | Production database |
| SQLite | Local development database |
| Pandas | Data processing |
| NumPy | Numerical operations |
| Scikit-learn | Machine Learning |
| HTML5 | Web page structure |
| CSS3 | Web page styling |
| JavaScript | Frontend interactions |
| Git and GitHub | Version control |
| Render | Application hosting |

## 🏗️ System Architecture

```text
             ┌─────────────────────────┐
             │        Users            │
             │ Student / Professor /   │
             │         Admin           │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │     Web Interface       │
             │      HTML / CSS         │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │      Flask Backend      │
             │ Authentication & Logic  │
             └────────────┬────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │    PostgreSQL    │    │  ML Prediction   │
    │ Student Records  │    │  Model & Scaler  │
    │ Attendance Data  │    │                  │
    └──────────────────┘    └──────────────────┘

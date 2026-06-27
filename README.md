# University Course Management System

A role-based University Course Management System built with **Django** that digitizes core academic workflows including course management, enrollments, attendance, assessments, grading, and instructor/student dashboards.

> **Status:** 🚧 In Active Development

---

# Features

## Authentication & Authorization

* Role-based authentication
* Instructor dashboard
* Student dashboard
* Protected views and custom authorization decorators

---

## Academic Management

* Buildings and Departments
* Rooms and Class Scheduling
* Courses and Sections
* Semester Management
* Course Assignments
* Student Enrollment
* Credit hour validation

---

## Assessment & Grading

* Create and manage assessments
* Configurable assessment types
* Bulk marks upload using Django FormSets
* Grade calculation
* GPA calculation
* Percentage calculation
* Assessment locking
* Validation to prevent invalid grading operations

---

## Attendance

* Create class sessions
* Mark attendance
* Attendance reports
* Attendance percentage calculation

---

## Instructor Dashboard

* Course management
* Assessment management
* Marks upload
* Gradebook
* Attendance management

---

## Student Portal

* View enrolled courses
* Attendance summary
* Grades
* Semester performance

---

## Technologies

* Python
* Django
* SQLite
* HTML
* Tailwind CSS
* JavaScript
* Git & GitHub

---

# Project Structure

```text
apps/
│
├── accounts/
├── academics/
├── finance/
└── ...
```

---

# Database Design

The project follows a normalized relational schema.

Core entities include:

* Student
* Instructor
* Department
* Course
* Section
* Enrollment
* Semester
* Assessment
* MarkEntry
* Attendance
* ClassSession

---

# Business Rules

Examples include:

* Students cannot exceed semester credit limits.
* Assessments must match the course type.
* Marks cannot exceed assessment totals.
* Inactive enrollments cannot receive grades.
* Locked assessments cannot be modified.
* Attendance cannot be recorded for unenrolled students.

---

# Future Enhancements

* Django REST Framework API
* React Frontend
* Announcements with attachments
* Course resources
* Transcript generation
* Email notifications
* Analytics dashboard
* Automated testing
* Docker deployment

---

# Installation

```bash
git clone <repository-url>

cd University-CMS

python -m venv venv

source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

---

# Screenshots

> Screenshots will be added as the project progresses.

---

# License

This project is intended for educational and portfolio purposes.

# University-CMS

> A role-based Django university system for course management, grading, and scheduling.

![GitHub stars](https://img.shields.io/github/stars/SufyanMalikT/University-CMS?style=for-the-badge&logo=github) ![GitHub forks](https://img.shields.io/github/forks/SufyanMalikT/University-CMS?style=for-the-badge&logo=github) ![GitHub issues](https://img.shields.io/github/issues/SufyanMalikT/University-CMS?style=for-the-badge&logo=github) ![Last commit](https://img.shields.io/github/last-commit/SufyanMalikT/University-CMS?style=for-the-badge&logo=github) ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 📑 Table of Contents

- [Description](#description)
- [Key Features](#key-features)
- [Use Cases](#use-cases)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Key Dependencies](#key-dependencies)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Contributors](#contributors)
- [Contributing](#contributing)

## 📝 Description

University Course Management System is a Django-powered web application designed to centralize and automate administrative and academic workflows in higher education. It addresses operational bottlenecks by organizing infrastructure like buildings, departments, and classrooms, and managing academic essentials such as student enrollments, course scheduling, and credit hour validations.

## ✨ Key Features

- **🔐 Role-Based Security** — Implements custom authorization decorators and protected views to secure distinct student and instructor dashboards.
- **🏫 Academic Infrastructure Management** — Models departments, classrooms, semesters, and course sections to establish schedules and coordinate room assignments.
- **📝 Configurable Grading & FormSets** — Supports bulk marks upload via Django FormSets alongside automated grade calculation, GPA assessment, and grade locking.
- **📊 Attendance Monitoring** — Tracks student attendance against specific class sessions and automatically calculates cumulative attendance percentages.
- **⚖️ Strict Business Validation** — Prevents invalid academic entries by validating semester credit limits, grade ranges, and assessment types.

## 🎯 Use Cases

- Setting up an integrated campus portal where administrators manage classes, schedules, and student enrollment records.
- Providing instructors with a dashboard to manage course gradebooks, record daily attendance, and perform bulk marks uploads.
- Enabling students to track their enrolled courses, monitor attendance thresholds, and view current semester GPA calculations.

## 📸 Screenshots

![cross](https://raw.githubusercontent.com/SufyanMalikT/University-CMS/main/static/app1/img/cross.png)

![hamb menu](https://raw.githubusercontent.com/SufyanMalikT/University-CMS/main/static/app1/img/hamb-menu.png)

## 🛠️ Tech Stack

- 🐍 **Python**

## ⚡ Quick Start

```bash

# 1. Clone the repository
git clone https://github.com/SufyanMalikT/University-CMS.git

# 2. Create & activate a virtualenv
python -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## 📦 Key Dependencies

```
arabic-reshaper: 3.0.0
asgiref: 3.11.0
asn1crypto: 1.5.1
certifi: 2026.1.4
cffi: 2.0.0
charset-normalizer: 3.4.4
cryptography: 46.0.4
cssselect2: 0.8.0
Django: 6.0.1
django-environ: 0.12.0
djangorestframework: 3.16.1
freetype-py: 2.5.1
html5lib: 1.1
idna: 3.11
lxml: 6.0.2
```

## 📁 Project Structure

```
.
├── apps
│   ├── academics
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms
│   │   │   └── instructor_forms.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_initial.py
│   │   │   ├── 0003_datesheetentry_exam_type_and_more.py
│   │   │   ├── 0004_datesheetentry_semester.py
│   │   │   ├── 0005_semester_is_admit_card_published_and_more.py
│   │   │   ├── 0006_alter_datesheetentry_course_by_section.py
│   │   │   ├── 0007_classschedule_room.py
│   │   │   ├── 0008_course_category.py
│   │   │   ├── 0009_courseassignment_result_uploaded.py
│   │   │   ├── 0010_alter_courseassignment_result_uploaded.py
│   │   │   ├── 0011_assessmenttype_alter_markentry_unique_together_and_more.py
│   │   │   ├── 0012_alter_markentry_assessment.py
│   │   │   ├── 0013_coursebysection_semester.py
│   │   │   ├── 0014_alter_coursebysection_semester_and_more.py
│   │   │   ├── 0015_assessmenttype_is_requried.py
│   │   │   ├── 0016_assessmenttype_is_unique.py
│   │   │   ├── 0017_semester_grading_deadline.py
│   │   │   ├── 0018_remove_markentry_is_locked.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── services
│   │   │   ├── instructor_services.py
│   │   │   └── student_services.py
│   │   ├── templates
│   │   │   └── temps
│   │   │       └── academics
│   │   │           └── ...
│   │   ├── templatetags
│   │   │   ├── __init__.py
│   │   │   └── instructor_tags.py
│   │   ├── tests.py
│   │   ├── urls
│   │   │   ├── instructor_urls.py
│   │   │   └── student_urls.py
│   │   └── views
│   │       ├── instructor_views.py
│   │       └── student_views.py
│   ├── accounts
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_student_roll_no.py
│   │   │   ├── 0003_student_department.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── services.py
│   │   ├── templates
│   │   │   ├── InstructorRegistration.html
│   │   │   ├── StudentRegistration.html
│   │   │   ├── base.html
│   │   │   └── login.html
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── signals.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   └── finance
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── migrations
│       │   ├── 0001_initial.py
│       │   ├── 0002_ledger_description_alter_ledger_transaction_type.py
│       │   ├── 0003_alter_ledger_payment_reference.py
│       │   └── __init__.py
│       ├── models.py
│       ├── services.py
│       ├── student_urls.py
│       ├── templates
│       │   ├── FeeReceipts.html
│       │   └── pdfs
│       │       ├── receipt_template.html
│       │       └── voucher_template.html
│       ├── tests.py
│       ├── utils
│       │   ├── FeeVoucher.py
│       │   └── semester.py
│       ├── views.py
│       └── webhooks.py
├── db.sqlite3
├── manage.py
├── practice
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt
├── static
│   └── app1
│       └── img
│           ├── cross.png
│           └── hamb-menu.png
└── templates
    ├── BaseInstructorDashboard.html
    ├── BaseStudentDashboard.html
    ├── base.html
    ├── comps
    │   ├── InstructorDashboard
    │   │   ├── messagebanner.html
    │   │   ├── navbar.html
    │   │   └── sidebar.html
    │   ├── StudentDashboard
    │   │   ├── navbar.html
    │   │   └── sidebar.html
    │   └── messagebanner.html
    └── error.html
```

## 🛠️ Development Setup

### Python
1. Install Python (v3.10+ recommended)
2. `python -m venv venv && source venv/bin/activate`  (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`

## 👥 Contributors

Thanks to everyone who has contributed to this project:

<p align="left">
<a href="https://github.com/SufyanMalikT" title="SufyanMalikT"><img src="https://avatars.githubusercontent.com/u/131298555?v=4&s=64" width="64" height="64" alt="SufyanMalikT" style="border-radius:50%" /></a>
</p>

[See the full list of contributors →](https://github.com/SufyanMalikT/University-CMS/graphs/contributors)

## 👥 Contributing

Contributions are welcome! Here's the standard flow:

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/SufyanMalikT/University-CMS.git`
3. **Branch**: `git checkout -b feature/your-feature`
4. **Commit**: `git commit -m 'feat: add some feature'`
5. **Push**: `git push origin feature/your-feature`
6. **Open** a pull request

Please follow the existing code style and include tests for new behavior where applicable.

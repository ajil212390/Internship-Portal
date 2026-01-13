---
description: Setup and run the integrated Django project (SISTMS)
---

# Smart Internship & Skill Training Management System (SISTMS)

## Integrated Django Project Setup Guide

This project integrates three separate Django projects (admin_side, student_side, academic_coordinator) into a single unified system.

---

## Prerequisites

- Python 3.10+ installed
- pip package manager
- Git (optional)

---

## Setup Instructions

### 1. Navigate to Project Directory

```bash
cd d:/OciuzProject/admin_side
```

### 2. Create Virtual Environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install django pillow
```

Or if requirements.txt exists:
```bash
pip install -r requirements.txt
```

### 4. Generate Migrations for New Models

// turbo
```bash
python manage.py makemigrations batches
python manage.py makemigrations accounts
python manage.py makemigrations attendance
python manage.py makemigrations certificates
```

### 5. Apply All Migrations

// turbo
```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create username, email, and password.

### 7. Run Development Server

// turbo
```bash
python manage.py runserver
```

The server will start at: http://127.0.0.1:8000/

---

## URL Structure

| Role | URL | Description |
|------|-----|-------------|
| Login | `/login/` | Unified login for all roles |
| Register | `/register/` | Student registration (pending approval) |
| Student Dashboard | `/student/dashboard/` | Student portal |
| Coordinator Dashboard | `/coordinator/dashboard/` | Coordinator portal |
| Admin Dashboard | `/admin/dashboard/` | Admin panel |
| Django Admin | `/admin/` | Built-in Django admin |

---

## User Roles

### 1. ADMIN
- Manage institutions, batches, courses, internships
- Assign multiple coordinators to batches
- Issue/approve certificates
- View all reports

### 2. COORDINATOR
- View pending student registrations and approve/reject
- View pending course/internship applications and approve/reject
- Mark attendance (MORNING/EVENING) for students
- View attendance report and eligible list (≥75%) for certificate

### 3. STUDENT
- Requires approval before login
- Apply for courses/internships
- View attendance percentage per course
- Download certificate only if eligible (≥75% attendance) and issued

---

## Key Workflows

### Student Registration & Approval Flow

1. Student visits `/register/`
2. Fills form: username, email, password, institution, batch (optional)
3. Account created with `approval_status = PENDING`
4. Coordinator views pending students at `/coordinator/students/?status=pending`
5. Coordinator approves or rejects with reason
6. If approved, student can login and access `/student/dashboard/`

### Application Workflow

1. Approved student browses programs at `/student/programs/`
2. Student applies for a course or internship
3. Application created with `status = PENDING`
4. Coordinator views applications at `/coordinator/applications/`
5. Coordinator approves/rejects
6. If approved, student is "enrolled"

### Attendance Workflow

1. Coordinator goes to `/coordinator/attendance/mark/`
2. Selects date and session (MORNING or EVENING)
3. Marks attendance for enrolled students
4. Each day can have 2 attendance records per student (morning + evening)
5. Student views attendance at `/student/attendance/`

### Certificate Eligibility

1. Student must have approved enrollment
2. Attendance percentage must be ≥75%
3. Admin/Coordinator can view eligible students
4. Admin issues certificate from Django admin or certificates page
5. Student downloads certificate at `/student/certificates/`

---

## Batch Management

### Creating Batches (Admin)

1. Go to `/admin/batches/`
2. Click "Add New Batch"
3. Fill: name, institution, description
4. Select multiple coordinators (checkbox selection)
5. Set start/end dates and max students
6. Save

### Assigning Coordinators to Batches

- One batch can have ONE OR MORE coordinators
- Coordinators can manage all students in their assigned batches
- Use the batch edit page to add/remove coordinators

---

## Database

Using SQLite by default (`db.sqlite3`).

To reset database:
```bash
# Delete db.sqlite3 file
python manage.py migrate
python manage.py createsuperuser
```

---

## Project Structure

```
admin_side/
├── manage.py
├── smart_internship/        # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── accounts/                # Authentication & user management
├── batches/                 # NEW: Batch management with multi-coordinator
├── institutions/            # Institution management
├── courses/                 # Course management
├── internships/             # Internship management
├── applications/            # Student applications/enrollments
├── attendance/              # MORNING/EVENING attendance
├── certificates/            # Certificate with 75% eligibility
├── dashboard/               # Admin dashboard
├── templates/
│   ├── admin/               # Admin templates
│   ├── coordinator/         # Coordinator templates
│   └── student/             # Student templates
└── static/                  # CSS, JS, images
```

---

## Testing Credentials

After creating superuser, you can:

1. Login as Admin (superuser) at `/login/`
2. Create an Institution at `/admin/institutions/add/`
3. Create a Batch at `/admin/batches/add/`
4. Create a Coordinator at `/admin/coordinators/add/`
5. Register a test student at `/register/`
6. Login as Coordinator, approve the student
7. Login as Student, apply for courses

---

## Troubleshooting

### Migration Conflicts
```bash
python manage.py makemigrations --merge
python manage.py migrate
```

### Static Files Not Loading
```bash
python manage.py collectstatic
```

### Reset All Migrations
```bash
# Delete all migration files (except __init__.py) in each app's migrations folder
# Delete db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

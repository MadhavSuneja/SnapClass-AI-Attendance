import bcrypt                     # Password security
from .config import supabase      # Database connection


def hash_pass(pwd):
    # Hash password
    return bcrypt.hashpw(
        pwd.encode(),             # Convert bytes
        bcrypt.gensalt()          # Random salt
    ).decode()                    # Convert string


def check_pass(pwd, hashed):
    # Verify password
    return bcrypt.checkpw(
        pwd.encode(),             # User password
        hashed.encode()           # Saved password
    )


def check_teacher_exists(username):
    # Check username
    response = (
        supabase.table("teachers")    # Teachers table
        .select("username")           # Get username
        .eq("username", username)     # Match username
        .execute()                    # Run query
    )

    return len(response.data) > 0     # Exists or not


def create_teacher(username, password, name):
    # Teacher data
    data = {
        "username": username,             # Username
        "password": hash_pass(password),  # Secure password
        "name": name,                     # Teacher name
    }

    response = (
        supabase.table("teachers")    # Teachers table
        .insert(data)                 # Insert record
        .execute()                    # Run query
    )

    return response.data              # Return teacher


def teacher_login(username, password):
    # Find teacher
    response = (
        supabase.table("teachers")    # Teachers table
        .select("*")                  # Get all data
        .eq("username", username)     # Match username
        .execute()                    # Run query
    )

    if response.data:
        teacher = response.data[0]    # First teacher

        if check_pass(
            password,
            teacher["password"]
        ):
            return teacher            # Login success

    return None                       # Login failed


def get_all_students():
    # Fetch students
    response = (
        supabase.table("students")
        .select("*")
        .execute()
    )

    return response.data


def create_student(
    new_name,
    face_embedding=None,
    voice_embedding=None
):
    # Student data
    data = {
        "name": new_name,                 # Student name
        "face_embedding": face_embedding, # Face vector
        "voice_embedding": voice_embedding # Voice vector
    }

    response = (
        supabase.table("students")
        .insert(data)
        .execute()
    )

    return response.data


def create_subject(
    subject_code,
    name,
    section,
    teacher_id
):
    # Subject data
    data = {
        "subject_code": subject_code, # Subject code
        "name": name,                 # Subject name
        "section": section,           # Class section
        "teacher_id": teacher_id,     # Teacher id
    }

    response = (
        supabase.table("subjects")
        .insert(data)
        .execute()
    )

    return response.data


def get_teacher_subjects(teacher_id):
    # Teacher subjects
    response = (
        supabase.table("subjects")
        .select(
            "*, "
            "subject_students(count), "
            "attendance_logs(timestamp)"
        )
        .eq("teacher_id", teacher_id)
        .execute()
    )

    subjects = response.data or []

    for sub in subjects:

        # Student count
        sub["total_students"] = (
            sub.get(
                "subject_students",
                [{}]
            )[0].get("count", 0)
            if sub.get("subject_students")
            else 0
        )

        attendance = sub.get(
            "attendance_logs",
            []
        )

        # Unique classes
        unique_sessions = len(
            set(
                log["timestamp"]
                for log in attendance
            )
        )

        sub["total_classes"] = (
            unique_sessions
        )

        # Remove extra data
        sub.pop(
            "subject_students",
            None
        )

        sub.pop(
            "attendance_logs",
            None
        )

    return subjects


def enroll_student_to_subject(
    student_id,
    subject_id
):
    # Enrollment data
    data = {
        "student_id": student_id,
        "subject_id": subject_id,
    }

    response = (
        supabase.table(
            "subject_students"
        )
        .insert(data)
        .execute()
    )

    return response.data


def unenroll_student_to_subject(
    student_id,
    subject_id
):
    # Remove enrollment
    response = (
        supabase.table(
            "subject_students"
        )
        .delete()
        .eq(
            "student_id",
            student_id
        )
        .eq(
            "subject_id",
            subject_id
        )
        .execute()
    )

    return response.data


def get_student_subjects(student_id):
    # Student subjects
    response = (
        supabase.table(
            "subject_students"
        )
        .select(
            "*, subjects(*)"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    return response.data


def get_student_attendance(student_id):
    # Attendance history
    response = (
        supabase.table(
            "attendance_logs"
        )
        .select(
            "*, subjects(*)"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    return response.data


def create_attendance(logs):
    # Save attendance
    response = (
        supabase.table(
            "attendance_logs"
        )
        .insert(logs)
        .execute()
    )

    return response.data


def get_attendance_for_teacher(
    teacher_id
):
    # Teacher attendance
    response = (
        supabase.table(
            "attendance_logs"
        )
        .select(
            "*, subjects!inner(*)"
        )
        .eq(
            "subjects.teacher_id",
            teacher_id
        )
        .execute()
    )

    return response.data
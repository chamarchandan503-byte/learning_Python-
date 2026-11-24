"""
student.py - Student Management Module.

Provides core student functions for backward compatibility with existing scripts,
while seamlessly leveraging the enhanced domain models and persistence engine.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from models import Student, SubjectScore, AttendanceRecord, FeeRecord
from storage import StorageManager
from manager import StudentManager
import ui

DATA_FILE = Path(__file__).with_name("students.json")
_storage = StorageManager(Path(__file__).parent)
_manager = StudentManager(_storage)


def load_students() -> List[Dict[str, Any]]:
    """
    Load student records from JSON file.
    Returns a list of student dictionaries for backward compatibility.
    """
    _manager.reload()
    students_list = _manager.get_all_students()
    return [s.to_dict() for s in students_list]


def save_students(students: List[Dict[str, Any]]) -> None:
    """
    Save all student records to JSON file.
    Accepts list of dictionaries or Student objects.
    """
    converted: List[Student] = []
    for item in students:
        if isinstance(item, Student):
            converted.append(item)
        elif isinstance(item, dict):
            converted.append(Student.from_dict(item))

    _storage.save_students(converted)
    _manager.reload()


def add_student(students: List[Dict[str, Any]], roll: str, name: str, marks: float) -> None:
    """
    Add a new student with roll number, name, and initial marks.
    Updates the provided list and saves to disk.
    """
    roll_clean = str(roll).strip()
    name_clean = str(name).strip()

    if any(str(s.get("roll") or s.get("roll_number")) == roll_clean for s in students):
        print("Error: Roll number already exists!")
        return

    if not name_clean:
        print("Error: Student name cannot be empty!")
        return

    try:
        marks_val = float(marks)
    except (ValueError, TypeError):
        print("Error: Marks must be a valid number!")
        return

    if not (0.0 <= marks_val <= 100.0):
        print("Error: Marks must be between 0 and 100!")
        return

    student = Student(
        roll_number=roll_clean,
        name=name_clean,
        course="Computer Science",
        semester=1,
    )
    student.add_or_update_subject("General Studies", marks_val, 100.0)

    # Add to list
    s_dict = student.to_dict()
    students.append(s_dict)
    save_students(students)

    print(f"Student '{name_clean}' (Roll: {roll_clean}) added successfully!")


def view_students(students: List[Dict[str, Any]]) -> None:
    """
    Display all students in a clean, formatted presentation.
    """
    if not students:
        print("No student records found.")
        return

    # Convert to Student objects for rich table rendering
    student_objs = [
        s if isinstance(s, Student) else Student.from_dict(s)
        for s in students
    ]

    headers = ["Roll Number", "Student Name", "Course", "Marks %", "CGPA", "Grade", "Status"]
    rows = []
    for s in student_objs:
        rows.append([
            s.roll_number,
            s.name,
            s.course,
            f"{s.overall_percentage:5.1f}%",
            f"{s.cgpa:4.2f}",
            s.grade,
            s.result_status
        ])

    ui.draw_table(headers, rows, alignments=["L", "L", "L", "R", "R", "C", "C"], title="ALL STUDENTS")


def search_student(students: List[Dict[str, Any]], roll: str) -> Optional[Dict[str, Any]]:
    """
    Find a student by roll number and display details.
    """
    roll_clean = str(roll).strip()

    for s in students:
        s_roll = str(s.get("roll") or s.get("roll_number", "")).strip()
        if s_roll == roll_clean:
            s_obj = s if isinstance(s, Student) else Student.from_dict(s)
            print("\nStudent Found!")
            print(f"Roll Number : {s_obj.roll_number}")
            print(f"Name        : {s_obj.name}")
            print(f"Course      : {s_obj.course}")
            print(f"Marks %     : {s_obj.overall_percentage}%")
            print(f"CGPA        : {s_obj.cgpa}")
            print(f"Grade       : {s_obj.grade}")
            print(f"Attendance  : {s_obj.attendance.percentage}%")
            print(f"Fee Status  : {s_obj.fees.status}")
            return s

    print("Student not found!")
    return None


def update_marks(students: List[Dict[str, Any]], roll: str, new_marks: float) -> bool:
    """
    Update a student's marks.
    """
    roll_clean = str(roll).strip()

    try:
        marks_val = float(new_marks)
    except (ValueError, TypeError):
        print("Error: Marks must be a valid number!")
        return False

    if not (0.0 <= marks_val <= 100.0):
        print("Error: Marks must be between 0 and 100!")
        return False

    for s in students:
        s_roll = str(s.get("roll") or s.get("roll_number", "")).strip()
        if s_roll == roll_clean:
            s_obj = s if isinstance(s, Student) else Student.from_dict(s)
            s_obj.add_or_update_subject("General Studies", marks_val, 100.0)

            # Update dict in-place
            updated_dict = s_obj.to_dict()
            s.clear()
            s.update(updated_dict)

            save_students(students)
            print(f"Marks for {s_obj.name} updated to {marks_val}/100 successfully!")
            return True

    print("Student not found!")
    return False


def delete_student(students: List[Dict[str, Any]], roll: str) -> bool:
    """
    Delete a student by roll number.
    """
    roll_clean = str(roll).strip()

    for s in students:
        s_roll = str(s.get("roll") or s.get("roll_number", "")).strip()
        if s_roll == roll_clean:
            students.remove(s)
            save_students(students)
            print("Student deleted successfully!")
            return True

    print("Student not found!")
    return False


# Module self-test or standalone runner
if __name__ == "__main__":
    records = load_students()
    print(f"Loaded {len(records)} student records.")
    view_students(records)

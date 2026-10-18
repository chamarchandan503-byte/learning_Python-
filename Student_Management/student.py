
# student.py
# Student Management System

import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("students.json")


def load_students():
    """Load student records from JSON file."""

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Student data must be a list.")

        for student in data:
            if not isinstance(student, dict):
                raise ValueError("Invalid student record.")

            if not {"roll", "name", "marks"}.issubset(student):
                raise ValueError("Student record is incomplete.")

        return data

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot read students.json: {error}"
        ) from error


def save_students(students):
    """Save all student records."""

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(students, file, indent=4)


def add_student(students, roll, name, marks):
    """Add a new student."""

    if any(s["roll"] == roll for s in students):
        print("Error: Roll number already exists!")
        return

    if not name.strip():
        print("Error: Student name cannot be empty!")
        return

    if not 0 <= marks <= 100:
        print("Error: Marks must be between 0 and 100!")
        return

    student = {
        "roll": roll,
        "name": name.strip(),
        "marks": marks
    }

    students.append(student)
    save_students(students)

    print("Student added successfully!")


def view_students(students):
    """Display all students."""

    if not students:
        print("No student records found.")
        return

    print("\n--- Student Records ---")

    for student in students:
        print(f"Roll Number: {student['roll']}")
        print(f"Name: {student['name']}")
        print(f"Marks: {student['marks']}/100")
        print("-" * 25)


def search_student(students, roll):
    """Find a student by roll number."""

    for student in students:
        if student["roll"] == roll:
            print("\nStudent Found!")
            print(f"Roll Number: {student['roll']}")
            print(f"Name: {student['name']}")
            print(f"Marks: {student['marks']}/100")
            return

    print("Student not found!")


def update_marks(students, roll, new_marks):
    """Update a student's marks."""

    if not 0 <= new_marks <= 100:
        print("Marks must be between 0 and 100!")
        return

    for student in students:
        if student["roll"] == roll:
            student["marks"] = new_marks
            save_students(students)
            print("Marks updated successfully!")
            return

    print("Student not found!")


def delete_student(students, roll):
    """Delete a student by roll number."""

    for student in students:
        if student["roll"] == roll:
            students.remove(student)
            save_students(students)
            print("Student deleted successfully!")
            return

    print("Student not found!")

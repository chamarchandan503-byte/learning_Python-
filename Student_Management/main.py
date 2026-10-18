
# main.py
# Student Management System

import student

try:
    students = student.load_students()
except RuntimeError as error:
    print(error)
    print("Please fix students.json before continuing.")
    raise SystemExit(1)


while True:
    print("\n===== STUDENT MANAGEMENT SYSTEM =====")
    print("1. Add Student")
    print("2. View All Students")
    print("3. Search Student")
    print("4. Update Student Marks")
    print("5. Delete Student")
    print("6. Exit")

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        roll = input("Enter Roll Number: ").strip()
        name = input("Enter Student Name: ").strip()

        try:
            marks = float(input("Enter Marks (0-100): "))
            student.add_student(students, roll, name, marks)
        except ValueError:
            print("Please enter valid numeric marks.")

    elif choice == "2":
        student.view_students(students)

    elif choice == "3":
        roll = input("Enter Roll Number to Search: ").strip()
        student.search_student(students, roll)

    elif choice == "4":
        roll = input("Enter Roll Number: ").strip()

        try:
            marks = float(input("Enter New Marks: "))
            student.update_marks(students, roll, marks)
        except ValueError:
            print("Please enter valid numeric marks.")

    elif choice == "5":
        roll = input("Enter Roll Number to Delete: ").strip()
        student.delete_student(students, roll)

    elif choice == "6":
        print("Thank you for using Student Management System!")
        break

    else:
        print("Invalid choice! Please try again.")

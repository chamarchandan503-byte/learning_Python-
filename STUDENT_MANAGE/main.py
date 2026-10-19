
import json
import os

FILE_NAME = "students.json"

# File se students ka data load karna
def load_students():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            print("Warning: File read nahi ho payi. Empty records use honge.")
    return []


students = load_students()


# Data ko file mein save karna
def save_students():
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(students, file, indent=4, ensure_ascii=False)


# 1. Student add karna
def add_student():
    name = input("Student ka naam: ").strip()
    roll = input("Roll number: ").strip()

    if not name or not roll:
        print("Name aur roll number dono zaroori hain.")
        return

    if any(s["roll"] == roll for s in students):
        print("Ye roll number pahle se maujood hai.")
        return

    students.append({"name": name, "roll": roll})
    save_students()
    print("Student successfully add ho gaya!")


# 2. Sabhi students dekhna
def view_students():
    if not students:
        print("Abhi koi student record nahi hai.")
        return

    print("\n--- STUDENT RECORDS ---")
    for student in students:
        print("Name:", student["name"])
        print("Roll Number:", student["roll"])
        print("-----------------------")


# 3. Student search karna
def search_student():
    roll = input("Search karne ke liye roll number: ").strip()

    for student in students:
        if student["roll"] == roll:
            print("Student mil gaya!")
            print("Name:", student["name"])
            print("Roll Number:", student["roll"])
            return

    print("Student nahi mila.")


# 4. Student record update karna
def update_student():
    roll = input("Update karne ke liye roll number: ").strip()

    for student in students:
        if student["roll"] == roll:
            new_name = input(
                "Naya naam (same rakhne ke liye Enter): "
            ).strip()

            new_roll = input(
                "Naya roll number (same rakhne ke liye Enter): "
            ).strip()

            if new_roll and any(
                s["roll"] == new_roll and s is not student
                for s in students
            ):
                print("Ye roll number kisi aur student ka hai.")
                return

            if new_name:
                student["name"] = new_name

            if new_roll:
                student["roll"] = new_roll

            save_students()
            print("Student record update ho gaya!")
            return

    print("Student nahi mila.")


# 5. Student delete karna
def delete_student():
    roll = input("Delete karne ke liye roll number: ").strip()

    for student in students:
        if student["roll"] == roll:
            confirm = input(
                "Kya aap delete karna chahte hain? (yes/no): "
            ).strip().lower()

            if confirm == "yes":
                students.remove(student)
                save_students()
                print("Student record delete ho gaya!")
            else:
                print("Delete cancel kar diya gaya.")
            return

    print("Student nahi mila.")


# Shuru mein Chandan ka record ek baar add karna
if not any(s["roll"] == "2504650100008" for s in students):
    students.append({
        "name": "Chandan",
        "roll": "2504650100008"
    })
    save_students()


# Main menu
while True:
    print("\n===== STUDENT MANAGEMENT SYSTEM =====")
    print("1. Add Student")
    print("2. View All Students")
    print("3. Search Student")
    print("4. Update Student")
    print("5. Delete Student")
    print("6. Exit")

    choice = input("Apna option chuniye (1-6): ").strip()

    if choice == "1":
        add_student()
    elif choice == "2":
        view_students()
    elif choice == "3":
        search_student()
    elif choice == "4":
        update_student()
    elif choice == "5":
        delete_student()
    elif choice == "6":
        print("Program band ho raha hai. Data save hai.")
        break
    else:
        print("Invalid option! 1 se 6 ke beech chuniye.")

# Sample students ko ek baar add karna
sample_students = [
    {"name": "Chandan", "roll": "2504650100008"},
    {"name": "Rahul Kumar", "roll": "2504650100009"},
    {"name": "Aman Kumar", "roll": "2504650100010"},
    {"name": "Priya Kumari", "roll": "2504650100011"},
    {"name": "Neha Kumari", "roll": "2504650100012"},
    {"name": "Rohit Kumar", "roll": "2504650100013"}
]

for sample in sample_students:
    if not any(s["roll"] == sample["roll"] for s in students):
        students.append(sample)

save_students()

"""
main.py - Student Management & Academic Information System.

Interactive CLI application with full CRUD capabilities, academic analytics,
printable transcripts, data backups, and CSV export/import.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import List, Optional

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from models import Student, SubjectScore, AttendanceRecord, FeeRecord
from storage import StorageManager
from manager import StudentManager
import ui
from ui import C


def render_student_table(students: List[Student], title: str = "STUDENT RECORDS") -> None:
    """Render a standard student directory table."""
    headers = ["Roll No", "Student Name", "Course / Dept", "Sem", "Marks %", "CGPA", "Grade", "Att %", "Fee Status", "Status"]
    rows = []

    for s in students:
        fee_color = C.GREEN if s.fees.status == "PAID" else (C.YELLOW if s.fees.status == "PARTIAL" else C.RED)
        att_color = C.RED if s.attendance.is_shortage else C.GREEN
        grade_color = C.GREEN if s.grade in ("A+", "A") else (C.YELLOW if s.grade in ("B+", "B") else C.RED)

        rows.append([
            s.roll_number,
            s.name,
            s.course,
            f"Sem-{s.semester}",
            f"{s.overall_percentage:5.1f}%",
            f"{s.cgpa:4.2f}",
            f"{grade_color}{s.grade}{C.RESET}",
            f"{att_color}{s.attendance.percentage:5.1f}%{C.RESET}",
            f"{fee_color}{s.fees.status}{C.RESET}",
            s.status
        ])

    ui.draw_table(
        headers=headers,
        rows=rows,
        alignments=["L", "L", "L", "C", "R", "R", "C", "R", "C", "C"],
        title=title
    )


# --- Action Handlers ---

def handle_view_directory(mgr: StudentManager) -> None:
    """Display student directory with sorting controls."""
    ui.clear_screen()
    ui.print_section_header("Student Directory & Registry", "📋")

    students = mgr.get_all_students()
    if not students:
        ui.print_warning("No students currently registered in the system.")
        ui.pause()
        return

    render_student_table(students, f"ALL REGISTERED STUDENTS (Total: {len(students)})")

    print(f"\n{C.CYAN}{C.BOLD}Sorting Options:{C.RESET}")
    print("  [1] Roll Number (Default)  [2] Name (A-Z)  [3] Percentage (High-Low)")
    print("  [4] CGPA (High-Low)        [5] Attendance  [6] Department / Course")
    print("  [Enter] Keep default & continue")

    sort_choice = input(f"{C.BOLD}Select sort option [1-6]: {C.RESET}").strip()
    sort_map = {
        "1": "roll",
        "2": "name",
        "3": "percentage",
        "4": "cgpa",
        "5": "attendance",
        "6": "course",
    }

    if sort_choice in sort_map:
        sorted_list = mgr.get_all_students(sort_by=sort_map[sort_choice])
        ui.clear_screen()
        ui.print_section_header(f"Directory - Sorted by {sort_map[sort_choice].upper()}", "📋")
        render_student_table(sorted_list, f"SORTED BY: {sort_map[sort_choice].upper()}")

    ui.pause()


def handle_enroll_student(mgr: StudentManager) -> None:
    """Interactive guided student enrollment."""
    ui.clear_screen()
    ui.print_banner()
    ui.print_section_header("Enroll New Student", "➕")

    roll = ui.prompt_string("Enter Student Roll / Registration Number")
    if mgr.get_student(roll):
        ui.print_error(f"A student with roll number '{roll}' already exists.")
        ui.pause()
        return

    name = ui.prompt_string("Enter Full Student Name")
    course = ui.prompt_string("Enter Course / Branch", default="B.Tech Computer Science")
    semester = ui.prompt_int("Enter Current Semester (1-8)", default=1, min_val=1, max_val=8)
    email = ui.prompt_string("Enter Email Address", default=f"{name.lower().replace(' ', '.')}@college.edu")
    phone = ui.prompt_string("Enter Contact Phone Number", default="9876543210")

    student = Student(
        roll_number=roll,
        name=name,
        course=course,
        semester=semester,
        email=email,
        phone=phone,
    )

    # Prompt for initial academic subjects
    print(f"\n{C.CYAN}Academic Performance Setup:{C.RESET}")
    add_subs = ui.prompt_confirm("Do you want to enter initial subject marks now?", default=True)
    if add_subs:
        default_subs = [
            "Programming in Python",
            "Data Structures & Algorithms",
            "Database Systems",
            "Computer Networks",
        ]
        for sub in default_subs:
            include = ui.prompt_confirm(f"Add subject '{sub}'?", default=True)
            if include:
                score = ui.prompt_float(f"Enter marks obtained in {sub} (0-100)", min_val=0.0, max_val=100.0)
                student.add_or_update_subject(sub, score, 100.0)

        # Allow custom subjects
        while True:
            more = ui.prompt_confirm("Add an additional custom subject?", default=False)
            if not more:
                break
            c_name = ui.prompt_string("Subject Name")
            c_score = ui.prompt_float(f"Marks obtained in {c_name} (0-100)", min_val=0.0, max_val=100.0)
            student.add_or_update_subject(c_name, c_score, 100.0)

    # Attendance Setup
    print(f"\n{C.CYAN}Attendance Setup:{C.RESET}")
    total_cls = ui.prompt_int("Total lectures conducted", default=100, min_val=1)
    att_cls = ui.prompt_int(f"Lectures attended (max {total_cls})", default=85, min_val=0, max_val=total_cls)
    student.attendance = AttendanceRecord(total_classes=total_cls, attended_classes=att_cls)

    # Fee Setup
    print(f"\n{C.CYAN}Fee Structure Setup:{C.RESET}")
    tot_fee = ui.prompt_float("Total Semester Fee (INR)", default=60000.0, min_val=0.0)
    paid_fee = ui.prompt_float("Amount Paid (INR)", default=60000.0, min_val=0.0, max_val=tot_fee)
    student.fees = FeeRecord(total_fee=tot_fee, paid_amount=paid_fee)

    success, msg = mgr.add_student(student)
    if success:
        ui.print_success(msg)
        print(f"  Overall Percentage: {student.overall_percentage}% | Grade: {student.grade} | CGPA: {student.cgpa}")
    else:
        ui.print_error(msg)

    ui.pause()


def handle_search_students(mgr: StudentManager) -> None:
    """Universal search across roll, name, department, status."""
    ui.clear_screen()
    ui.print_section_header("Search Student Records", "🔍")

    query = ui.prompt_string("Enter search term (Roll No, Name, Course, or Grade)")
    results = mgr.search(query)

    if not results:
        ui.print_warning(f"No student matches found for '{query}'.")
        ui.pause()
        return

    ui.print_success(f"Found {len(results)} matching student(s):")
    render_student_table(results, f"SEARCH RESULTS FOR: '{query}'")

    # Quick action: View report card
    print(f"\n{C.CYAN}Options:{C.RESET}")
    print("  Enter a Roll Number to view the student's full Academic Transcript.")
    print("  Press [Enter] to return to Main Menu.")

    chosen_roll = input(f"{C.BOLD}Enter Roll Number (or press Enter): {C.RESET}").strip()
    if chosen_roll:
        target = mgr.get_student(chosen_roll)
        if target:
            ui.display_report_card(target)
        else:
            ui.print_error(f"Student with roll number '{chosen_roll}' not found.")

    ui.pause()


def handle_update_profile(mgr: StudentManager) -> None:
    """Update personal and enrollment profile details."""
    ui.clear_screen()
    ui.print_section_header("Update Student Profile", "✏️")

    roll = ui.prompt_string("Enter Roll Number to update")
    student = mgr.get_student(roll)
    if not student:
        ui.print_error(f"Student '{roll}' not found.")
        ui.pause()
        return

    print(f"\n{C.BOLD}Current Profile Details for {student.name} ({student.roll_number}):{C.RESET}")
    print(f"  Name    : {student.name}")
    print(f"  Course  : {student.course}")
    print(f"  Semester: {student.semester}")
    print(f"  Email   : {student.email}")
    print(f"  Phone   : {student.phone}")
    print(f"  Status  : {student.status}")

    print(f"\n{C.DIM}(Press Enter on any field to keep existing value){C.RESET}")
    new_name = ui.prompt_string("Full Name", default=student.name)
    new_course = ui.prompt_string("Course / Department", default=student.course)
    new_sem = ui.prompt_int("Semester", default=student.semester, min_val=1, max_val=8)
    new_email = ui.prompt_string("Email", default=student.email)
    new_phone = ui.prompt_string("Phone", default=student.phone)

    print("Statuses: [1] ACTIVE  [2] INACTIVE  [3] GRADUATED  [Enter] Keep Current")
    st_choice = input(f"{C.BOLD}Select Status option: {C.RESET}").strip()
    status_map = {"1": "ACTIVE", "2": "INACTIVE", "3": "GRADUATED"}
    new_status = status_map.get(st_choice, student.status)

    success, msg = mgr.update_student_profile(
        roll_number=roll,
        name=new_name,
        course=new_course,
        semester=new_sem,
        email=new_email,
        phone=new_phone,
        status=new_status,
    )

    if success:
        ui.print_success(msg)
    else:
        ui.print_error(msg)

    ui.pause()


def handle_manage_subjects(mgr: StudentManager) -> None:
    """Manage subject marks: add, edit, or remove subjects."""
    ui.clear_screen()
    ui.print_section_header("Manage Subject Marks & Evaluations", "📝")

    roll = ui.prompt_string("Enter Student Roll Number")
    student = mgr.get_student(roll)
    if not student:
        ui.print_error(f"Student '{roll}' not found.")
        ui.pause()
        return

    while True:
        ui.clear_screen()
        ui.print_section_header(f"Academic Marks for: {student.name} ({student.roll_number})", "📝")

        # Show current subjects
        sub_headers = ["#", "Subject Name", "Max Marks", "Marks Obtained", "Percentage", "Grade", "Status"]
        sub_rows = []
        for idx, sub in enumerate(student.subjects.values(), 1):
            sub_rows.append([
                str(idx),
                sub.subject_name,
                f"{sub.max_marks:.0f}",
                f"{sub.marks_obtained:.1f}",
                f"{sub.percentage:5.1f}%",
                sub.grade,
                "PASS" if sub.is_pass else "FAIL"
            ])
        ui.draw_table(sub_headers, sub_rows, alignments=["C", "L", "R", "R", "R", "C", "C"])
        print(f"  Overall: {student.overall_percentage}% | CGPA: {student.cgpa} | Result: {student.result_status}\n")

        print(f"{C.CYAN}{C.BOLD}Subject Actions:{C.RESET}")
        print("  [1] Add or Update Subject Marks")
        print("  [2] Remove a Subject")
        print("  [0] Done / Back to Main Menu")

        choice = input(f"{C.BOLD}Choose action [0-2]: {C.RESET}").strip()

        if choice == "1":
            sub_name = ui.prompt_string("Enter Subject Name")
            curr_score = student.subjects.get(sub_name).marks_obtained if sub_name in student.subjects else 0.0
            score = ui.prompt_float(f"Enter Marks for '{sub_name}' (0-100)", default=curr_score, min_val=0.0, max_val=100.0)
            ok, msg = mgr.update_subject_marks(roll, sub_name, score, 100.0)
            if ok:
                ui.print_success(msg)
            else:
                ui.print_error(msg)
            ui.pause()

        elif choice == "2":
            sub_name = ui.prompt_string("Enter Subject Name to Remove")
            ok, msg = mgr.remove_subject_marks(roll, sub_name)
            if ok:
                ui.print_success(msg)
            else:
                ui.print_error(msg)
            ui.pause()

        elif choice == "0":
            break


def handle_attendance_and_fees(mgr: StudentManager) -> None:
    """Update attendance metrics and fee payment records."""
    ui.clear_screen()
    ui.print_section_header("Attendance & Tuition Fee Administration", "📅")

    roll = ui.prompt_string("Enter Student Roll Number")
    student = mgr.get_student(roll)
    if not student:
        ui.print_error(f"Student '{roll}' not found.")
        ui.pause()
        return

    print(f"\n{C.BOLD}Student: {student.name} ({student.roll_number}){C.RESET}")
    print(f"  Current Attendance: {student.attendance.attended_classes} / {student.attendance.total_classes} classes ({student.attendance.percentage}%)")
    print(f"  Fee Status        : {student.fees.status} | Total: Rs. {student.fees.total_fee:,.2f} | Paid: Rs. {student.fees.paid_amount:,.2f} | Due: Rs. {student.fees.due_amount:,.2f}")

    print(f"\n{C.CYAN}Options:{C.RESET}")
    print("  [1] Update Attendance (Attended / Total classes)")
    print("  [2] Record Tuition Fee Payment")
    print("  [3] Adjust Total Fee Structure")
    print("  [0] Cancel / Back")

    choice = input(f"{C.BOLD}Choose action [0-3]: {C.RESET}").strip()

    if choice == "1":
        tot = ui.prompt_int("Total classes held", default=student.attendance.total_classes, min_val=1)
        att = ui.prompt_int("Classes attended", default=student.attendance.attended_classes, min_val=0, max_val=tot)
        ok, msg = mgr.update_attendance(roll, att, tot)
        if ok:
            ui.print_success(msg)
        else:
            ui.print_error(msg)

    elif choice == "2":
        if student.fees.due_amount <= 0:
            ui.print_success("Fees are already fully paid! No dues pending.")
        else:
            print(f"Current pending dues: Rs. {student.fees.due_amount:,.2f}")
            amt = ui.prompt_float("Payment amount received (INR)", min_val=1.0, max_val=student.fees.due_amount)
            ok, msg = mgr.record_fee_payment(roll, amt)
            if ok:
                ui.print_success(msg)
            else:
                ui.print_error(msg)

    elif choice == "3":
        new_tot = ui.prompt_float("New Total Semester Fee (INR)", default=student.fees.total_fee, min_val=0.0)
        student.fees.total_fee = new_tot
        mgr._persist()
        ui.print_success(f"Total fee updated to Rs. {new_tot:,.2f}. Current dues: Rs. {student.fees.due_amount:,.2f}")

    ui.pause()


def handle_view_transcript(mgr: StudentManager) -> None:
    """Render official printable transcript / report card."""
    ui.clear_screen()
    ui.print_section_header("Official Academic Transcript Generator", "📜")

    roll = ui.prompt_string("Enter Student Roll Number to generate Report Card")
    student = mgr.get_student(roll)
    if not student:
        ui.print_error(f"Student with roll number '{roll}' not found.")
        ui.pause()
        return

    ui.display_report_card(student)

    # Option to save transcript to a text file
    save_file = ui.prompt_confirm("Do you want to save this transcript to a text file?", default=False)
    if save_file:
        out_filename = f"transcript_{student.roll_number}.txt"
        out_path = Path(__file__).resolve().parent / out_filename
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("       OFFICIAL ACADEMIC TRANSCRIPT & PERFORMANCE REPORT\n")
                f.write("=" * 70 + "\n")
                f.write(f"Student Name : {student.name}\n")
                f.write(f"Roll Number  : {student.roll_number}\n")
                f.write(f"Course/Dept  : {student.course} (Sem-{student.semester})\n")
                f.write(f"Status       : {student.status}\n")
                f.write("-" * 70 + "\n")
                f.write(f"{'Subject':<32} {'Max':<8} {'Obtained':<10} {'Grade':<8} {'Status'}\n")
                f.write("-" * 70 + "\n")
                for sub in student.subjects.values():
                    f.write(f"{sub.subject_name:<32} {sub.max_marks:<8.0f} {sub.marks_obtained:<10.1f} {sub.grade:<8} {'PASS' if sub.is_pass else 'FAIL'}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Total Marks Obtained: {student.total_marks_obtained:.1f} / {student.total_max_marks:.1f}\n")
                f.write(f"Overall Percentage  : {student.overall_percentage:.2f}%\n")
                f.write(f"Cumulative CGPA     : {student.cgpa:.2f} / 10.0\n")
                f.write(f"Letter Grade        : {student.grade}\n")
                f.write(f"Result Status       : {student.result_status}\n")
                f.write(f"Attendance          : {student.attendance.attended_classes}/{student.attendance.total_classes} ({student.attendance.percentage}%)\n")
                f.write(f"Fee Balance Status  : {student.fees.status} (Due: Rs. {student.fees.due_amount:.2f})\n")
                f.write("=" * 70 + "\n")
            ui.print_success(f"Transcript exported to '{out_filename}'.")
        except Exception as err:
            ui.print_error(f"Failed to export transcript: {err}")

    ui.pause()


def handle_leaderboard(mgr: StudentManager) -> None:
    """Display academic ranks, topper highlight, and leaderboard."""
    ui.clear_screen()
    ui.print_section_header("Academic Leaderboard & Merit Rankings", "🏆")

    ranked = mgr.get_leaderboard(limit=15)
    if not ranked:
        ui.print_warning("No evaluated students available for rankings.")
        ui.pause()
        return

    topper = mgr.get_topper()
    if topper:
        print(f"\n{C.YELLOW}{C.BOLD}🌟 CLASS TOPPER & GOLD MEDALIST: {topper.name} ({topper.roll_number}) 🌟")
        print(f"   Department: {topper.course} | Score: {topper.overall_percentage}% | CGPA: {topper.cgpa}{C.RESET}\n")

    headers = ["Rank", "Roll No", "Student Name", "Course / Dept", "Percentage", "CGPA", "Grade", "Status"]
    rows = []

    badge_map = {1: "🥇 1st", 2: "🥈 2nd", 3: "🥉 3rd"}

    for rank, s in ranked:
        rank_str = badge_map.get(rank, f"   {rank}th")
        rows.append([
            rank_str,
            s.roll_number,
            s.name,
            s.course,
            f"{s.overall_percentage:5.1f}%",
            f"{s.cgpa:4.2f}",
            s.grade,
            s.result_status
        ])

    ui.draw_table(headers, rows, alignments=["C", "L", "L", "L", "R", "R", "C", "C"], title="ACADEMIC MERIT LIST")
    ui.pause()


def handle_analytics(mgr: StudentManager) -> None:
    """Display comprehensive class statistics, subject averages, and histogram."""
    ui.clear_screen()
    ui.print_section_header("Comprehensive Academic Analytics & Insights", "📈")

    stats = mgr.get_class_statistics()
    if stats["total_students"] == 0:
        ui.print_warning("No student records available for analytics.")
        ui.pause()
        return

    print(f"\n{C.BOLD}┌─ INSTITUTIONAL METRICS SUMMARY " + "─" * 46 + "┐")
    print(f"│  Total Enrolled Students: {stats['total_students']:<6} │  Overall Pass Rate       : {stats['pass_percentage']:5.1f}%")
    print(f"│  Passed Students        : {stats['passed_count']:<6} │  Distinction Students    : {stats['distinction_count']:<6}")
    print(f"│  Failed / Arrears       : {stats['failed_count']:<6} │  Average Class Percentage: {stats['average_percentage']:5.1f}%")
    print(f"│  Highest Score Obtained : {stats['highest_percentage']:5.1f}% │  Lowest Score Obtained   : {stats['lowest_percentage']:5.1f}%")
    print(f"│  Average Attendance     : {stats['average_attendance']:5.1f}% │  Low Attendance (<75%)   : {stats['attendance_shortage_count']:<6}")
    print(f"│  Total Fees Collected   : Rs. {stats['total_fees_collected']:>10,.2f} │  Pending Fee Dues        : Rs. {stats['total_fees_due']:>10,.2f}")
    print("└" + "─" * 78 + f"┘{C.RESET}")

    # Subject-wise analytics table
    sub_analytics = mgr.get_subject_analytics()
    if sub_analytics:
        sub_headers = ["Subject Name", "Enrolled", "Average %", "Highest %", "Lowest %", "Pass Rate"]
        sub_rows = []
        for sname, sdata in sub_analytics.items():
            sub_rows.append([
                sname,
                str(sdata["enrolled_count"]),
                f"{sdata['average_percentage']:5.1f}%",
                f"{sdata['highest']:5.1f}%",
                f"{sdata['lowest']:5.1f}%",
                f"{sdata['pass_rate']:5.1f}%",
            ])
        ui.draw_table(sub_headers, sub_rows, alignments=["L", "C", "R", "R", "R", "R"], title="SUBJECT EVALUATION BENCHMARKS")

    # Grade distribution chart
    grade_dist = mgr.get_grade_distribution()
    ui.render_grade_distribution_chart(grade_dist)

    ui.pause()


def handle_defaulters_and_alerts(mgr: StudentManager) -> None:
    """Display critical attendance shortage warnings and fee dues."""
    ui.clear_screen()
    ui.print_section_header("Defaulters & Risk Alerts", "⚠️")

    # 1. Attendance Shortage
    shortage_list = mgr.filter_by_attendance_shortage(75.0)
    print(f"\n{C.RED}{C.BOLD}1. ATTENDANCE SHORTAGE (< 75% REQUIREMENT) - {len(shortage_list)} Student(s):{C.RESET}")

    if not shortage_list:
        ui.print_success("No attendance defaulters! All students have attended 75% or more classes.")
    else:
        att_headers = ["Roll No", "Student Name", "Course", "Total Classes", "Attended", "Attendance %", "Deficit Classes"]
        att_rows = []
        for s in shortage_list:
            # Classes needed to reach 75%
            # (attended + x) / (total + x) >= 0.75 => x >= 3*total - 4*attended
            deficit = max(0, 3 * s.attendance.total_classes - 4 * s.attendance.attended_classes)
            att_rows.append([
                s.roll_number,
                s.name,
                s.course,
                str(s.attendance.total_classes),
                str(s.attendance.attended_classes),
                f"{C.RED}{s.attendance.percentage:5.1f}%{C.RESET}",
                f"{deficit} more needed",
            ])
        ui.draw_table(att_headers, att_rows, alignments=["L", "L", "L", "C", "C", "R", "L"])

    # 2. Fee Defaulters
    fee_defaulters = mgr.filter_by_fee_defaulters()
    print(f"\n{C.YELLOW}{C.BOLD}2. PENDING TUITION FEE DUES - {len(fee_defaulters)} Student(s):{C.RESET}")

    if not fee_defaulters:
        ui.print_success("No pending tuition fee dues! All accounts are fully cleared.")
    else:
        fee_headers = ["Roll No", "Student Name", "Course", "Total Fee", "Paid Amount", "Pending Due", "Status"]
        fee_rows = []
        for s in fee_defaulters:
            fee_rows.append([
                s.roll_number,
                s.name,
                s.course,
                f"Rs. {s.fees.total_fee:,.2f}",
                f"Rs. {s.fees.paid_amount:,.2f}",
                f"{C.RED}Rs. {s.fees.due_amount:,.2f}{C.RESET}",
                s.fees.status
            ])
        ui.draw_table(fee_headers, fee_rows, alignments=["L", "L", "L", "R", "R", "R", "C"])

    ui.pause()


def handle_data_management(mgr: StudentManager) -> None:
    """Export to CSV/JSON, Import from CSV, Backups, and Audit Logs."""
    ui.clear_screen()
    ui.print_section_header("Data Management & Archival Suite", "💾")

    print("  [1] Export All Students to CSV (Excel compatible)")
    print("  [2] Import Students from CSV File")
    print("  [3] Create Instant Timestamped Snapshot Backup")
    print("  [4] View Recent System Audit Logs")
    print("  [0] Back to Main Menu")

    choice = input(f"\n{C.BOLD}Select Data Management option [0-4]: {C.RESET}").strip()

    if choice == "1":
        ok, msg = mgr.storage.export_to_csv()
        if ok:
            ui.print_success(msg)
        else:
            ui.print_error(msg)

    elif choice == "2":
        csv_file = ui.prompt_string("Enter CSV file path to import", default="students_import.csv")
        target = Path(csv_file)
        if not target.is_absolute():
            target = mgr.storage.base_dir / csv_file

        if not target.exists():
            ui.print_error(f"File '{target}' was not found.")
        else:
            imported, skipped, errors = mgr.storage.import_from_csv(target)
            ui.print_success(f"Import finished: {imported} added, {skipped} skipped.")
            if errors:
                print(f"{C.YELLOW}Import Notes:{C.RESET}")
                for err in errors[:10]:
                    print(f"  • {err}")
            mgr.reload()

    elif choice == "3":
        ok, msg = mgr.storage.create_manual_backup()
        if ok:
            ui.print_success(msg)
        else:
            ui.print_error(msg)

    elif choice == "4":
        logs = mgr.storage.get_recent_logs(limit=15)
        if not logs:
            ui.print_info("No audit logs recorded yet.")
        else:
            log_headers = ["Timestamp", "Action", "Roll / Target", "Details"]
            log_rows = [[entry["timestamp"], entry["action"], entry["roll_number"], entry["details"]] for entry in logs]
            ui.draw_table(log_headers, log_rows, alignments=["L", "L", "L", "L"], title="AUDIT ACTIVITY TRAIL")

    ui.pause()


def handle_delete_student(mgr: StudentManager) -> None:
    """Safe student record deletion with double-confirmation."""
    ui.clear_screen()
    ui.print_section_header("Delete / Deregister Student", "🗑️")

    roll = ui.prompt_string("Enter Roll Number to delete")
    student = mgr.get_student(roll)
    if not student:
        ui.print_error(f"Student with roll number '{roll}' does not exist.")
        ui.pause()
        return

    print(f"\n{C.RED}{C.BOLD}CAUTION: You are about to permanently delete this student record:{C.RESET}")
    print(f"  Roll Number: {student.roll_number}")
    print(f"  Name       : {student.name}")
    print(f"  Course     : {student.course} (Sem-{student.semester})")
    print(f"  Marks %    : {student.overall_percentage}% | CGPA: {student.cgpa}")

    confirm = ui.prompt_confirm(f"Are you sure you want to delete {student.name}?", default=False)
    if not confirm:
        ui.print_info("Deletion cancelled. No changes made.")
        ui.pause()
        return

    ok, msg = mgr.delete_student(roll)
    if ok:
        ui.print_success(msg)
    else:
        ui.print_error(msg)

    ui.pause()


# --- Main Application Loop ---

def main() -> None:
    """Application entrypoint."""
    storage = StorageManager()
    mgr = StudentManager(storage)

    # Seed initial sample data if the repository has fewer than 5 records
    mgr.seed_sample_data_if_empty()

    while True:
        ui.clear_screen()
        ui.print_banner()

        stats = mgr.get_class_statistics()
        print(f"  {C.DIM}Active Database:{C.RESET} {stats['total_students']} Students Registered  |  "
              f"{C.DIM}Class Average:{C.RESET} {stats['average_percentage']}%  |  "
              f"{C.DIM}Pass Rate:{C.RESET} {stats['pass_percentage']}%\n")

        print(f"{C.CYAN}{C.BOLD}CORE MODULES:{C.RESET}")
        print("  [1]  📋 Student Directory        - View, browse & sort all enrolled students")
        print("  [2]  ➕ Enroll New Student       - Register student with profile & subjects")
        print("  [3]  🔍 Search Records           - Universal search across roll, name, course")
        print("  [4]  ✏️  Update Profile          - Modify personal details, course, semester")
        print("  [5]  📝 Manage Subject Marks     - Add, edit, or remove subject score cards")
        print("  [6]  📅 Attendance & Fee Dues    - Track lecture attendance & tuition payments")

        print(f"\n{C.YELLOW}{C.BOLD}ACADEMIC REPORTS & ANALYTICS:{C.RESET}")
        print("  [7]  📜 Official Report Card     - Generate printable academic transcript")
        print("  [8]  🏆 Leaderboard & Ranks      - Class topper, top 10 merit rankings")
        print("  [9]  📈 Performance Analytics   - Class statistics & grade histogram chart")
        print("  [10] ⚠️  Defaulters & Alerts      - Low attendance (<75%) & pending fee dues")

        print(f"\n{C.GREEN}{C.BOLD}SYSTEM & ARCHIVAL:{C.RESET}")
        print("  [11] 💾 Data Management          - CSV export/import, snapshot backup, audit trail")
        print("  [12] 🗑️  Delete Student Record   - Safely remove student with confirmation")
        print("  [0]  🚪 Exit Application\n")

        choice = input(f"{C.BOLD}Enter your choice [0-12]: {C.RESET}").strip()

        if choice == "1":
            handle_view_directory(mgr)
        elif choice == "2":
            handle_enroll_student(mgr)
        elif choice == "3":
            handle_search_students(mgr)
        elif choice == "4":
            handle_update_profile(mgr)
        elif choice == "5":
            handle_manage_subjects(mgr)
        elif choice == "6":
            handle_attendance_and_fees(mgr)
        elif choice == "7":
            handle_view_transcript(mgr)
        elif choice == "8":
            handle_leaderboard(mgr)
        elif choice == "9":
            handle_analytics(mgr)
        elif choice == "10":
            handle_defaulters_and_alerts(mgr)
        elif choice == "11":
            handle_data_management(mgr)
        elif choice == "12":
            handle_delete_student(mgr)
        elif choice in ("0", "exit", "quit", "q"):
            ui.clear_screen()
            ui.print_banner()
            ui.print_success("Thank you for using Student Management & Academic Information System!")
            print(f"{C.DIM}All records and audit trails have been safely synchronized to disk.{C.RESET}\n")
            break
        else:
            ui.print_error("Invalid option! Please enter a number between 0 and 12.")
            ui.pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation interrupted by user. Exiting cleanly...")
        sys.exit(0)

    ui.pause()


# --- Main Application Loop ---

def main() -> None:
    """Application entrypoint."""
    storage = StorageManager()
    mgr = StudentManager(storage)

    # Seed initial sample data if the repository has fewer than 5 records
    mgr.seed_sample_data_if_empty()

    while True:
        ui.clear_screen()
        ui.print_banner()

        stats = mgr.get_class_statistics()
        print(f"  {C.DIM}Active Database:{C.RESET} {stats['total_students']} Students Registered  |  "
              f"{C.DIM}Class Average:{C.RESET} {stats['average_percentage']}%  |  "
              f"{C.DIM}Pass Rate:{C.RESET} {stats['pass_percentage']}%\n")

        print(f"{C.CYAN}{C.BOLD}CORE MODULES:{C.RESET}")
        print("  [1]  📋 Student Directory        - View, browse & sort all enrolled students")
        print("  [2]  ➕ Enroll New Student       - Register student with profile & subjects")
        print("  [3]  🔍 Search Records           - Universal search across roll, name, course")
        print("  [4]  ✏️  Update Profile          - Modify personal details, course, semester")
        print("  [5]  📝 Manage Subject Marks     - Add, edit, or remove subject score cards")
        print("  [6]  📅 Attendance & Fee Dues    - Track lecture attendance & tuition payments")

        print(f"\n{C.YELLOW}{C.BOLD}ACADEMIC REPORTS & ANALYTICS:{C.RESET}")
        print("  [7]  📜 Official Report Card     - Generate printable academic transcript")
        print("  [8]  🏆 Leaderboard & Ranks      - Class topper, top 10 merit rankings")
        print("  [9]  📈 Performance Analytics   - Class statistics & grade histogram chart")
        print("  [10] ⚠️  Defaulters & Alerts      - Low attendance (<75%) & pending fee dues")

        print(f"\n{C.GREEN}{C.BOLD}SYSTEM & ARCHIVAL:{C.RESET}")
        print("  [11] 💾 Data Management          - CSV export/import, snapshot backup, audit trail")
        print("  [12] 🗑️  Delete Student Record   - Safely remove student with confirmation")
        print("  [0]  🚪 Exit Application\n")

        choice = input(f"{C.BOLD}Enter your choice [0-12]: {C.RESET}").strip()

        if choice == "1":
            handle_view_directory(mgr)
        elif choice == "2":
            handle_enroll_student(mgr)
        elif choice == "3":
            handle_search_students(mgr)
        elif choice == "4":
            handle_update_profile(mgr)
        elif choice == "5":
            handle_manage_subjects(mgr)
        elif choice == "6":
            handle_attendance_and_fees(mgr)
        elif choice == "7":
            handle_view_transcript(mgr)
        elif choice == "8":
            handle_leaderboard(mgr)
        elif choice == "9":
            handle_analytics(mgr)
        elif choice == "10":
            handle_defaulters_and_alerts(mgr)
        elif choice == "11":
            handle_data_management(mgr)
        elif choice == "12":
            handle_delete_student(mgr)
        elif choice in ("0", "exit", "quit", "q"):
            ui.clear_screen()
            ui.print_banner()
            ui.print_success("Thank you for using Student Management & Academic Information System!")
            print(f"{C.DIM}All records and audit trails have been safely synchronized to disk.{C.RESET}\n")
            break
        else:
            ui.print_error("Invalid option! Please enter a number between 0 and 12.")
            ui.pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation interrupted by user. Exiting cleanly...")
        sys.exit(0)


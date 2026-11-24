"""
manager.py - Business Logic & Academic Analytics Engine.

Provides complete CRUD operations, multi-attribute querying, rank calculation,
subject statistics, fee auditing, and attendance tracking for students.
"""

from __future__ import annotations
import math
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from models import Student, SubjectScore, AttendanceRecord, FeeRecord
from storage import StorageManager


class StudentManager:
    """Core manager handling all business logic, queries, and analytics."""

    def __init__(self, storage: Optional[StorageManager] = None):
        self.storage = storage or StorageManager()
        self._students: Dict[str, Student] = {}
        self.reload()

    def reload(self) -> None:
        """Reload all students from the persistent storage layer."""
        students_list = self.storage.load_students()
        self._students = {s.roll_number: s for s in students_list}

    def _persist(self) -> bool:
        """Persist current in-memory students to disk."""
        return self.storage.save_students(list(self._students.values()))

    # --- CRUD Operations ---

    def add_student(self, student: Student) -> Tuple[bool, str]:
        """
        Add a new student to the system.
        Performs validation on roll number and name.
        """
        roll = student.roll_number.strip()
        if not roll:
            return False, "Roll number cannot be empty."

        if not student.name.strip():
            return False, "Student name cannot be empty."

        if roll in self._students:
            return False, f"A student with roll number '{roll}' already exists."

        student.roll_number = roll
        student.name = student.name.strip()
        self._students[roll] = student

        if self._persist():
            self.storage.log_activity("ADD_STUDENT", roll, f"Name: {student.name}, Course: {student.course}")
            return True, f"Student '{student.name}' (Roll: {roll}) successfully added!"
        else:
            return False, "Failed to save student data to disk."

    def get_student(self, roll_number: str) -> Optional[Student]:
        """Fetch a student by roll number (exact match)."""
        return self._students.get(roll_number.strip())

    def get_all_students(
        self,
        sort_by: str = "roll",
        reverse: bool = False
    ) -> List[Student]:
        """
        Get all students sorted by requested attribute:
        'roll', 'name', 'percentage', 'cgpa', 'attendance', 'dues', 'course'.
        """
        students = list(self._students.values())

        if sort_by == "name":
            students.sort(key=lambda s: s.name.lower(), reverse=reverse)
        elif sort_by in ("percentage", "marks"):
            students.sort(key=lambda s: s.overall_percentage, reverse=not reverse if not reverse else reverse)
        elif sort_by == "cgpa":
            students.sort(key=lambda s: s.cgpa, reverse=not reverse if not reverse else reverse)
        elif sort_by == "attendance":
            students.sort(key=lambda s: s.attendance.percentage, reverse=not reverse if not reverse else reverse)
        elif sort_by == "dues":
            students.sort(key=lambda s: s.fees.due_amount, reverse=not reverse if not reverse else reverse)
        elif sort_by == "course":
            students.sort(key=lambda s: (s.course.lower(), s.roll_number), reverse=reverse)
        else:
            # Default: sort by roll number (natural alphanumeric)
            def natural_sort_key(s: Student):
                try:
                    return (0, int(s.roll_number))
                except ValueError:
                    return (1, s.roll_number)
            students.sort(key=natural_sort_key, reverse=reverse)

        return students

    def update_student_profile(
        self,
        roll_number: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        course: Optional[str] = None,
        semester: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Update personal / academic profile details of a student."""
        student = self.get_student(roll_number)
        if not student:
            return False, f"Student with roll number '{roll_number}' not found."

        changes: List[str] = []
        if name is not None and name.strip():
            student.name = name.strip()
            changes.append("name")
        if email is not None:
            student.email = email.strip()
            changes.append("email")
        if phone is not None:
            student.phone = phone.strip()
            changes.append("phone")
        if course is not None and course.strip():
            student.course = course.strip()
            changes.append("course")
        if semester is not None and semester > 0:
            student.semester = semester
            changes.append("semester")
        if status is not None and status.strip():
            student.status = status.strip().upper()
            changes.append("status")

        if self._persist():
            self.storage.log_activity("UPDATE_PROFILE", roll_number, f"Updated: {', '.join(changes)}")
            return True, f"Profile for student '{student.name}' updated successfully."
        return False, "Failed to persist profile updates."

    def update_subject_marks(
        self,
        roll_number: str,
        subject_name: str,
        marks_obtained: float,
        max_marks: float = 100.0,
    ) -> Tuple[bool, str]:
        """Add or update subject marks for a student."""
        student = self.get_student(roll_number)
        if not student:
            return False, f"Student with roll number '{roll_number}' not found."

        try:
            student.add_or_update_subject(subject_name, marks_obtained, max_marks)
            if self._persist():
                self.storage.log_activity(
                    "UPDATE_MARKS",
                    roll_number,
                    f"Subject: {subject_name}, Marks: {marks_obtained}/{max_marks}"
                )
                return True, f"Subject '{subject_name}' updated ({marks_obtained}/{max_marks}) for {student.name}."
            return False, "Failed to save marks update to disk."
        except ValueError as err:
            return False, str(err)

    def remove_subject_marks(self, roll_number: str, subject_name: str) -> Tuple[bool, str]:
        """Remove a subject from a student's record."""
        student = self.get_student(roll_number)
        if not student:
            return False, f"Student '{roll_number}' not found."

        if student.remove_subject(subject_name):
            if self._persist():
                self.storage.log_activity("REMOVE_SUBJECT", roll_number, f"Removed {subject_name}")
                return True, f"Subject '{subject_name}' removed from {student.name}."
            return False, "Failed to save changes."
        return False, f"Subject '{subject_name}' not found for this student."

    def update_attendance(
        self,
        roll_number: str,
        attended: int,
        total: int,
    ) -> Tuple[bool, str]:
        """Update attendance metrics for a student."""
        student = self.get_student(roll_number)
        if not student:
            return False, f"Student '{roll_number}' not found."

        try:
            student.update_attendance(attended, total)
            if self._persist():
                self.storage.log_activity("UPDATE_ATTENDANCE", roll_number, f"{attended}/{total}")
                return True, f"Attendance updated: {attended}/{total} ({student.attendance.percentage}%)"
            return False, "Failed to save attendance update."
        except ValueError as err:
            return False, str(err)

    def record_fee_payment(
        self,
        roll_number: str,
        amount: float
    ) -> Tuple[bool, str]:
        """Record a tuition fee payment."""
        student = self.get_student(roll_number)
        if not student:
            return False, f"Student '{roll_number}' not found."

        try:
            student.record_fee_payment(amount)
            if self._persist():
                self.storage.log_activity("FEE_PAYMENT", roll_number, f"Amount: {amount}")
                return True, f"Payment of Rs. {amount:,.2f} recorded. Remaining due: Rs. {student.fees.due_amount:,.2f}"
            return False, "Failed to save fee payment."
        except ValueError as err:
            return False, str(err)

    def delete_student(self, roll_number: str) -> Tuple[bool, str]:
        """Delete a student record permanently."""
        roll = roll_number.strip()
        if roll not in self._students:
            return False, f"Student with roll number '{roll}' does not exist."

        deleted = self._students.pop(roll)
        if self._persist():
            self.storage.log_activity("DELETE_STUDENT", roll, f"Removed {deleted.name}")
            return True, f"Student '{deleted.name}' (Roll: {roll}) deleted successfully."
        else:
            # Revert in-memory pop if save failed
            self._students[roll] = deleted
            return False, "Failed to persist deletion to disk."

    # --- Querying, Filtering & Search ---

    def search(self, query: str) -> List[Student]:
        """
        Universal search matching query across roll number, name, course, email, and phone.
        Case-insensitive and substring match.
        """
        q = query.strip().lower()
        if not q:
            return self.get_all_students()

        results: List[Student] = []
        for s in self._students.values():
            if (
                q in s.roll_number.lower()
                or q in s.name.lower()
                or q in s.course.lower()
                or q in s.email.lower()
                or q in s.phone.lower()
                or q in s.result_status.lower()
                or q == s.grade.lower()
            ):
                results.append(s)

        return results

    def filter_by_course(self, course_name: str) -> List[Student]:
        """Filter students by course or department."""
        c = course_name.strip().lower()
        return [s for s in self._students.values() if c in s.course.lower()]

    def filter_by_attendance_shortage(self, threshold: float = 75.0) -> List[Student]:
        """Return all students whose attendance is strictly below the threshold."""
        return [s for s in self._students.values() if s.attendance.percentage < threshold]

    def filter_by_fee_defaulters(self) -> List[Student]:
        """Return all students who have pending fee dues."""
        return [s for s in self._students.values() if s.fees.due_amount > 0.0]

    def filter_by_grade(self, grade: str) -> List[Student]:
        """Return all students matching the given letter grade."""
        g = grade.strip().upper()
        return [s for s in self._students.values() if s.grade == g]

    # --- Analytics & Leaderboard ---

    def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, Student]]:
        """
        Calculate academic ranks based on overall percentage.
        Handles ties appropriately (e.g., 1, 2, 2, 4).
        """
        sorted_students = sorted(
            self._students.values(),
            key=lambda s: (s.overall_percentage, s.total_marks_obtained),
            reverse=True
        )

        ranked: List[Tuple[int, Student]] = []
        current_rank = 1
        for idx, student in enumerate(sorted_students):
            if idx > 0:
                prev_student = sorted_students[idx - 1]
                if student.overall_percentage < prev_student.overall_percentage:
                    current_rank = idx + 1
            ranked.append((current_rank, student))
            if limit and len(ranked) >= limit:
                break

        return ranked

    def get_topper(self) -> Optional[Student]:
        """Return the highest-scoring student in the institution."""
        if not self._students:
            return None
        return max(self._students.values(), key=lambda s: s.overall_percentage)

    def get_class_statistics(self) -> Dict[str, Any]:
        """
        Compute holistic class performance metrics:
        - Count, averages, high/low scores, pass/fail percentages, fee metrics.
        """
        total = len(self._students)
        if total == 0:
            return {
                "total_students": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pass_percentage": 0.0,
                "distinction_count": 0,
                "average_percentage": 0.0,
                "highest_percentage": 0.0,
                "lowest_percentage": 0.0,
                "average_attendance": 0.0,
                "attendance_shortage_count": 0,
                "total_fees_expected": 0.0,
                "total_fees_collected": 0.0,
                "total_fees_due": 0.0,
            }

        percentages = [s.overall_percentage for s in self._students.values()]
        attendances = [s.attendance.percentage for s in self._students.values()]
        passed_count = sum(1 for s in self._students.values() if s.result_status != "FAILED" and s.subjects)
        failed_count = sum(1 for s in self._students.values() if s.result_status == "FAILED")
        distinction_count = sum(1 for s in self._students.values() if s.result_status == "DISTINCTION")
        shortage_count = sum(1 for s in self._students.values() if s.attendance.is_shortage)

        total_expected_fee = sum(s.fees.total_fee for s in self._students.values())
        total_collected_fee = sum(s.fees.paid_amount for s in self._students.values())
        total_due_fee = sum(s.fees.due_amount for s in self._students.values())

        return {
            "total_students": total,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "distinction_count": distinction_count,
            "pass_percentage": round((passed_count / total) * 100.0, 2) if total > 0 else 0.0,
            "average_percentage": round(sum(percentages) / total, 2),
            "highest_percentage": max(percentages) if percentages else 0.0,
            "lowest_percentage": min(percentages) if percentages else 0.0,
            "average_attendance": round(sum(attendances) / total, 2),
            "attendance_shortage_count": shortage_count,
            "total_fees_expected": total_expected_fee,
            "total_fees_collected": total_collected_fee,
            "total_fees_due": total_due_fee,
        }

    def get_subject_analytics(self) -> Dict[str, Dict[str, Any]]:
        """
        Compute analytics per subject:
        number of students enrolled, average score, maximum score, minimum score, pass rate.
        """
        subjects_data: Dict[str, List[float]] = {}
        for s in self._students.values():
            for sub_name, score in s.subjects.items():
                if sub_name not in subjects_data:
                    subjects_data[sub_name] = []
                subjects_data[sub_name].append(score.percentage)

        analytics: Dict[str, Dict[str, Any]] = {}
        for sub_name, scores in subjects_data.items():
            cnt = len(scores)
            avg = round(sum(scores) / cnt, 2) if cnt > 0 else 0.0
            passed = sum(1 for sc in scores if sc >= 40.0)
            analytics[sub_name] = {
                "enrolled_count": cnt,
                "average_percentage": avg,
                "highest": max(scores) if scores else 0.0,
                "lowest": min(scores) if scores else 0.0,
                "pass_rate": round((passed / cnt) * 100.0, 2) if cnt > 0 else 0.0,
            }

        return analytics

    def get_grade_distribution(self) -> Dict[str, int]:
        """Count how many students belong to each letter grade."""
        dist = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for s in self._students.values():
            if s.subjects:
                dist[s.grade] = dist.get(s.grade, 0) + 1
        return dist

    # --- Sample Data Seeding ---

    def seed_sample_data_if_empty(self) -> bool:
        """
        If database has fewer than 2 records, pre-populates with realistic student data,
        including Chandan (2504650100008), Rahul, Aman, Priya, Neha, Rohit, etc.
        """
        if len(self._students) >= 5:
            return False

        samples = [
            Student(
                roll_number="2504650100008",
                name="Chandan Rao",
                email="chandan.rao@college.edu",
                phone="9876543210",
                course="B.Tech Computer Science",
                semester=4,
                subjects={
                    "Python Programming": SubjectScore("Python Programming", 96.0, 100.0),
                    "Data Structures & Algorithms": SubjectScore("Data Structures & Algorithms", 94.0, 100.0),
                    "Database Management Systems": SubjectScore("Database Management Systems", 92.0, 100.0),
                    "Operating Systems": SubjectScore("Operating Systems", 88.0, 100.0),
                    "Computer Networks": SubjectScore("Computer Networks", 90.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=115),
                fees=FeeRecord(total_fee=65000.0, paid_amount=65000.0),
                status="ACTIVE",
            ),
            Student(
                roll_number="101",
                name="Rahul Kumar",
                email="rahul.k@college.edu",
                phone="9812345671",
                course="B.Tech Computer Science",
                semester=4,
                subjects={
                    "Python Programming": SubjectScore("Python Programming", 85.0, 100.0),
                    "Data Structures & Algorithms": SubjectScore("Data Structures & Algorithms", 82.0, 100.0),
                    "Database Management Systems": SubjectScore("Database Management Systems", 80.0, 100.0),
                    "Operating Systems": SubjectScore("Operating Systems", 78.0, 100.0),
                    "Computer Networks": SubjectScore("Computer Networks", 84.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=102),
                fees=FeeRecord(total_fee=65000.0, paid_amount=50000.0),
                status="ACTIVE",
            ),
            Student(
                roll_number="102",
                name="Aman Kumar",
                email="aman.k@college.edu",
                phone="9823456782",
                course="B.Tech Computer Science",
                semester=4,
                subjects={
                    "Python Programming": SubjectScore("Python Programming", 90.0, 100.0),
                    "Data Structures & Algorithms": SubjectScore("Data Structures & Algorithms", 89.0, 100.0),
                    "Database Management Systems": SubjectScore("Database Management Systems", 91.0, 100.0),
                    "Operating Systems": SubjectScore("Operating Systems", 87.0, 100.0),
                    "Computer Networks": SubjectScore("Computer Networks", 88.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=110),
                fees=FeeRecord(total_fee=65000.0, paid_amount=65000.0),
                status="ACTIVE",
            ),
            Student(
                roll_number="103",
                name="Priya Kumari",
                email="priya.k@college.edu",
                phone="9834567893",
                course="B.Tech Information Technology",
                semester=4,
                subjects={
                    "Python Programming": SubjectScore("Python Programming", 88.0, 100.0),
                    "Data Structures & Algorithms": SubjectScore("Data Structures & Algorithms", 86.0, 100.0),
                    "Database Management Systems": SubjectScore("Database Management Systems", 93.0, 100.0),
                    "Web Technologies": SubjectScore("Web Technologies", 95.0, 100.0),
                    "Computer Networks": SubjectScore("Computer Networks", 89.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=118),
                fees=FeeRecord(total_fee=65000.0, paid_amount=65000.0),
                status="ACTIVE",
            ),
            Student(
                roll_number="104",
                name="Neha Kumari",
                email="neha.k@college.edu",
                phone="9845678904",
                course="B.Tech Computer Science",
                semester=4,
                subjects={
                    "Python Programming": SubjectScore("Python Programming", 76.0, 100.0),
                    "Data Structures & Algorithms": SubjectScore("Data Structures & Algorithms", 74.0, 100.0),
                    "Database Management Systems": SubjectScore("Database Management Systems", 79.0, 100.0),
                    "Operating Systems": SubjectScore("Operating Systems", 72.0, 100.0),
                    "Computer Networks": SubjectScore("Computer Networks", 75.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=82),  # Shortage warning! (68.3%)
                fees=FeeRecord(total_fee=65000.0, paid_amount=35000.0),  # Dues
                status="ACTIVE",
            ),
            Student(
                roll_number="105",
                name="Rohit Kumar",
                email="rohit.k@college.edu",
                phone="9856789015",
                course="B.Tech Mechanical Engineering",
                semester=4,
                subjects={
                    "Thermodynamics": SubjectScore("Thermodynamics", 68.0, 100.0),
                    "Fluid Mechanics": SubjectScore("Fluid Mechanics", 65.0, 100.0),
                    "Machine Design": SubjectScore("Machine Design", 70.0, 100.0),
                    "Manufacturing Tech": SubjectScore("Manufacturing Tech", 64.0, 100.0),
                    "Applied Mathematics": SubjectScore("Applied Mathematics", 72.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=120, attended_classes=98),
                fees=FeeRecord(total_fee=60000.0, paid_amount=60000.0),
                status="ACTIVE",
            ),
            Student(
                roll_number="106",
                name="Anjali Sharma",
                email="anjali.s@college.edu",
                phone="9867890126",
                course="Bachelor of Computer Applications",
                semester=2,
                subjects={
                    "C Programming": SubjectScore("C Programming", 92.0, 100.0),
                    "Digital Electronics": SubjectScore("Digital Electronics", 88.0, 100.0),
                    "Mathematics-II": SubjectScore("Mathematics-II", 90.0, 100.0),
                    "Communication Skills": SubjectScore("Communication Skills", 94.0, 100.0),
                },
                attendance=AttendanceRecord(total_classes=100, attended_classes=96),
                fees=FeeRecord(total_fee=45000.0, paid_amount=45000.0),
                status="ACTIVE",
            ),
        ]

        # Merge samples: do not overwrite existing roll numbers
        added_count = 0
        for sample in samples:
            if sample.roll_number not in self._students:
                self._students[sample.roll_number] = sample
                added_count += 1

        if added_count > 0:
            self._persist()
            self.storage.log_activity("SEED_DATA", "SYSTEM", f"Populated {added_count} sample student records.")
            return True
        return False

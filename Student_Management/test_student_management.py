"""
test_student_management.py - Comprehensive Unit Test Suite.

Tests domain models, grade & CGPA calculations, storage persistence,
CSV export/import, search filters, and academic analytics.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from models import (
    Student,
    SubjectScore,
    AttendanceRecord,
    FeeRecord,
    calculate_grade,
    calculate_cgpa,
)
from storage import StorageManager
from manager import StudentManager


class TestDomainCalculations(unittest.TestCase):
    """Test grade assignments and CGPA conversion formulas."""

    def test_grade_boundaries(self):
        self.assertEqual(calculate_grade(95.0), "A+")
        self.assertEqual(calculate_grade(90.0), "A+")
        self.assertEqual(calculate_grade(85.0), "A")
        self.assertEqual(calculate_grade(80.0), "A")
        self.assertEqual(calculate_grade(75.0), "B+")
        self.assertEqual(calculate_grade(65.0), "B")
        self.assertEqual(calculate_grade(55.0), "C")
        self.assertEqual(calculate_grade(45.0), "D")
        self.assertEqual(calculate_grade(39.9), "F")
        self.assertEqual(calculate_grade(0.0), "F")

    def test_cgpa_calculation(self):
        self.assertAlmostEqual(calculate_cgpa(95.0), 10.0, places=1)
        self.assertAlmostEqual(calculate_cgpa(85.5), 9.0, places=1)
        self.assertEqual(calculate_cgpa(0.0), 0.0)
        self.assertEqual(calculate_cgpa(100.0), 10.0)


class TestSubjectScore(unittest.TestCase):
    """Test SubjectScore data class."""

    def test_percentage_and_grade(self):
        sub = SubjectScore(subject_name="Python", marks_obtained=88.0, max_marks=100.0)
        self.assertEqual(sub.percentage, 88.0)
        self.assertEqual(sub.grade, "A")
        self.assertTrue(sub.is_pass)

    def test_fail_subject(self):
        sub = SubjectScore(subject_name="Maths", marks_obtained=32.0, max_marks=100.0)
        self.assertEqual(sub.percentage, 32.0)
        self.assertEqual(sub.grade, "F")
        self.assertFalse(sub.is_pass)


class TestAttendanceAndFees(unittest.TestCase):
    """Test Attendance and Fee domain logic."""

    def test_attendance_normal_and_shortage(self):
        att_ok = AttendanceRecord(total_classes=100, attended_classes=80)
        self.assertEqual(att_ok.percentage, 80.0)
        self.assertFalse(att_ok.is_shortage)

        att_bad = AttendanceRecord(total_classes=100, attended_classes=70)
        self.assertEqual(att_bad.percentage, 70.0)
        self.assertTrue(att_bad.is_shortage)

    def test_fee_dues_and_status(self):
        fee_paid = FeeRecord(total_fee=50000.0, paid_amount=50000.0)
        self.assertEqual(fee_paid.due_amount, 0.0)
        self.assertEqual(fee_paid.status, "PAID")

        fee_partial = FeeRecord(total_fee=50000.0, paid_amount=30000.0)
        self.assertEqual(fee_partial.due_amount, 20000.0)
        self.assertEqual(fee_partial.status, "PARTIAL")

        fee_pending = FeeRecord(total_fee=50000.0, paid_amount=0.0)
        self.assertEqual(fee_pending.due_amount, 50000.0)
        self.assertEqual(fee_pending.status, "PENDING")


class TestStudentModel(unittest.TestCase):
    """Test comprehensive Student object operations."""

    def setUp(self):
        self.student = Student(
            roll_number="101",
            name="Rahul Kumar",
            course="Computer Science",
            semester=3,
        )

    def test_multi_subject_metrics(self):
        self.student.add_or_update_subject("Python", 90.0, 100.0)
        self.student.add_or_update_subject("DSA", 80.0, 100.0)

        self.assertEqual(self.student.total_marks_obtained, 170.0)
        self.assertEqual(self.student.total_max_marks, 200.0)
        self.assertEqual(self.student.overall_percentage, 85.0)
        self.assertEqual(self.student.grade, "A")
        self.assertEqual(self.student.result_status, "DISTINCTION")

    def test_legacy_dict_conversion(self):
        legacy = {"roll": "205", "name": "Aman", "marks": 78.5}
        student = Student.from_dict(legacy)
        self.assertEqual(student.roll_number, "205")
        self.assertEqual(student.name, "Aman")
        self.assertEqual(student.overall_percentage, 78.5)
        self.assertIn("General Studies", student.subjects)

    def test_subject_validation(self):
        with self.assertRaises(ValueError):
            self.student.add_or_update_subject("", 50.0)
        with self.assertRaises(ValueError):
            self.student.add_or_update_subject("Physics", -10.0)
        with self.assertRaises(ValueError):
            self.student.add_or_update_subject("Physics", 150.0, 100.0)


class TestStorageAndPersistence(unittest.TestCase):
    """Test atomic file writing, backup creation, and CSV export."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(Path(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load(self):
        s1 = Student(roll_number="001", name="Alice")
        s1.add_or_update_subject("Math", 95.0, 100.0)
        s2 = Student(roll_number="002", name="Bob")

        ok = self.storage.save_students([s1, s2])
        self.assertTrue(ok)
        self.assertTrue(self.storage.data_file.exists())

        loaded = self.storage.load_students()
        self.assertEqual(len(loaded), 2)
        rolls = [s.roll_number for s in loaded]
        self.assertIn("001", rolls)
        self.assertIn("002", rolls)

    def test_csv_export_and_import(self):
        s1 = Student(roll_number="101", name="Charlie", course="IT", semester=2)
        s1.add_or_update_subject("Java", 88.0, 100.0)
        self.storage.save_students([s1])

        csv_file = Path(self.test_dir) / "test_export.csv"
        ok, msg = self.storage.export_to_csv(csv_file)
        self.assertTrue(ok)
        self.assertTrue(csv_file.exists())

        # Test CSV import in another storage instance
        new_dir = tempfile.mkdtemp()
        new_storage = StorageManager(Path(new_dir))
        imported, skipped, errors = new_storage.import_from_csv(csv_file)
        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 0)

        imported_students = new_storage.load_students()
        self.assertEqual(len(imported_students), 1)
        self.assertEqual(imported_students[0].name, "Charlie")
        shutil.rmtree(new_dir, ignore_errors=True)


class TestStudentManager(unittest.TestCase):
    """Test StudentManager CRUD, search, ranking, and analytics."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(Path(self.test_dir))
        self.manager = StudentManager(self.storage)

        # Add 3 students
        s1 = Student(roll_number="10", name="Chandan", course="CS")
        s1.add_or_update_subject("Python", 96.0, 100.0)

        s2 = Student(roll_number="20", name="Priya", course="IT")
        s2.add_or_update_subject("Python", 90.0, 100.0)

        s3 = Student(roll_number="30", name="Rohan", course="CS")
        s3.add_or_update_subject("Python", 70.0, 100.0)

        self.manager.add_student(s1)
        self.manager.add_student(s2)
        self.manager.add_student(s3)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_duplicate_roll_rejected(self):
        duplicate = Student(roll_number="10", name="Another Chandan")
        ok, msg = self.manager.add_student(duplicate)
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

    def test_search_and_filter(self):
        res = self.manager.search("Chandan")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].roll_number, "10")

        cs_students = self.manager.filter_by_course("CS")
        self.assertEqual(len(cs_students), 2)

    def test_leaderboard_and_topper(self):
        topper = self.manager.get_topper()
        self.assertIsNotNone(topper)
        self.assertEqual(topper.roll_number, "10")
        self.assertEqual(topper.name, "Chandan")

        ranks = self.manager.get_leaderboard()
        self.assertEqual(ranks[0][0], 1)
        self.assertEqual(ranks[0][1].name, "Chandan")
        self.assertEqual(ranks[1][0], 2)
        self.assertEqual(ranks[1][1].name, "Priya")

    def test_update_and_delete(self):
        ok, msg = self.manager.update_student_profile("10", name="Chandan Rao", semester=5)
        self.assertTrue(ok)
        updated = self.manager.get_student("10")
        self.assertEqual(updated.name, "Chandan Rao")
        self.assertEqual(updated.semester, 5)

        del_ok, _ = self.manager.delete_student("30")
        self.assertTrue(del_ok)
        self.assertIsNone(self.manager.get_student("30"))
        self.assertEqual(len(self.manager.get_all_students()), 2)

    def test_class_statistics(self):
        stats = self.manager.get_class_statistics()
        self.assertEqual(stats["total_students"], 3)
        self.assertEqual(stats["highest_percentage"], 96.0)
        self.assertEqual(stats["lowest_percentage"], 70.0)


if __name__ == "__main__":
    unittest.main()

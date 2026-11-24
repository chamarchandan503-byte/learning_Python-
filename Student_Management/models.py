"""
models.py - Domain Models for Student Management System.

Defines the core data structures and business logic for students,
including academic subjects, attendance records, fee status, and grade calculations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


def calculate_grade(percentage: float) -> str:
    """Calculate letter grade based on percentage."""
    if percentage >= 90.0:
        return "A+"
    elif percentage >= 80.0:
        return "A"
    elif percentage >= 70.0:
        return "B+"
    elif percentage >= 60.0:
        return "B"
    elif percentage >= 50.0:
        return "C"
    elif percentage >= 40.0:
        return "D"
    else:
        return "F"


def calculate_cgpa(percentage: float) -> float:
    """
    Calculate CGPA on a standard 10.0 scale.
    Formula: percentage / 9.5 (Standard CBSE / AICTE conversion), clamped [0.0, 10.0].
    """
    if percentage <= 0.0:
        return 0.0
    cgpa = round(percentage / 9.5, 2)
    return min(10.0, max(0.0, cgpa))


@dataclass
class SubjectScore:
    """Represents a student's score in a specific subject."""
    subject_name: str
    marks_obtained: float
    max_marks: float = 100.0

    @property
    def percentage(self) -> float:
        if self.max_marks <= 0:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100.0, 2)

    @property
    def grade(self) -> str:
        return calculate_grade(self.percentage)

    @property
    def is_pass(self) -> bool:
        return self.percentage >= 40.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_name": self.subject_name,
            "marks_obtained": self.marks_obtained,
            "max_marks": self.max_marks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubjectScore:
        return cls(
            subject_name=str(data.get("subject_name", "")),
            marks_obtained=float(data.get("marks_obtained", 0.0)),
            max_marks=float(data.get("max_marks", 100.0)),
        )


@dataclass
class AttendanceRecord:
    """Tracks attendance metrics for a student."""
    total_classes: int = 100
    attended_classes: int = 85

    @property
    def percentage(self) -> float:
        if self.total_classes <= 0:
            return 0.0
        return round((self.attended_classes / self.total_classes) * 100.0, 2)

    @property
    def is_shortage(self) -> bool:
        """True if attendance is strictly below standard requirement (75%)."""
        return self.percentage < 75.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_classes": self.total_classes,
            "attended_classes": self.attended_classes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AttendanceRecord:
        return cls(
            total_classes=int(data.get("total_classes", 100)),
            attended_classes=int(data.get("attended_classes", 85)),
        )


@dataclass
class FeeRecord:
    """Tracks tuition and fee payments for a student."""
    total_fee: float = 50000.0
    paid_amount: float = 50000.0

    @property
    def due_amount(self) -> float:
        return max(0.0, round(self.total_fee - self.paid_amount, 2))

    @property
    def status(self) -> str:
        if self.due_amount <= 0.0:
            return "PAID"
        elif self.paid_amount > 0.0:
            return "PARTIAL"
        return "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_fee": self.total_fee,
            "paid_amount": self.paid_amount,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeeRecord:
        return cls(
            total_fee=float(data.get("total_fee", 50000.0)),
            paid_amount=float(data.get("paid_amount", 50000.0)),
        )


@dataclass
class Student:
    """
    Comprehensive Student entity covering personal, academic,
    attendance, and administrative records.
    """
    roll_number: str
    name: str
    email: str = ""
    phone: str = ""
    course: str = "Computer Science"
    semester: int = 1
    subjects: Dict[str, SubjectScore] = field(default_factory=dict)
    attendance: AttendanceRecord = field(default_factory=AttendanceRecord)
    fees: FeeRecord = field(default_factory=FeeRecord)
    status: str = "ACTIVE"  # ACTIVE, INACTIVE, GRADUATED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # --- Academic Calculations ---

    @property
    def total_marks_obtained(self) -> float:
        """Sum of marks obtained across all subjects."""
        if not self.subjects:
            return 0.0
        return round(sum(s.marks_obtained for s in self.subjects.values()), 2)

    @property
    def total_max_marks(self) -> float:
        """Sum of maximum marks across all subjects."""
        if not self.subjects:
            return 0.0
        return round(sum(s.max_marks for s in self.subjects.values()), 2)

    @property
    def overall_percentage(self) -> float:
        """Overall percentage across all registered subjects."""
        if not self.subjects or self.total_max_marks <= 0:
            return 0.0
        return round((self.total_marks_obtained / self.total_max_marks) * 100.0, 2)

    @property
    def cgpa(self) -> float:
        """Calculated CGPA on a 10.0 scale."""
        return calculate_cgpa(self.overall_percentage)

    @property
    def grade(self) -> str:
        """Overall letter grade."""
        return calculate_grade(self.overall_percentage)

    @property
    def result_status(self) -> str:
        """Academic status: Passed with Distinction, First Class, Pass, or Fail."""
        if not self.subjects:
            return "N/A"
        # If student failed in any subject
        if any(not s.is_pass for s in self.subjects.values()):
            return "FAILED"
        if self.overall_percentage >= 75.0:
            return "DISTINCTION"
        elif self.overall_percentage >= 60.0:
            return "FIRST CLASS"
        elif self.overall_percentage >= 50.0:
            return "SECOND CLASS"
        else:
            return "PASSED"

    @property
    def marks(self) -> float:
        """
        Legacy compatibility property: returns overall percentage or single mark.
        """
        return self.overall_percentage

    # --- Mutation helpers ---

    def add_or_update_subject(
        self,
        subject_name: str,
        marks_obtained: float,
        max_marks: float = 100.0
    ) -> None:
        """Add or update a subject score."""
        name_clean = subject_name.strip()
        if not name_clean:
            raise ValueError("Subject name cannot be empty.")
        if marks_obtained < 0 or (max_marks > 0 and marks_obtained > max_marks):
            raise ValueError(f"Marks must be between 0 and {max_marks}.")

        self.subjects[name_clean] = SubjectScore(
            subject_name=name_clean,
            marks_obtained=round(marks_obtained, 2),
            max_marks=round(max_marks, 2),
        )
        self.updated_at = datetime.now().isoformat()

    def remove_subject(self, subject_name: str) -> bool:
        """Remove a subject score."""
        name_clean = subject_name.strip()
        if name_clean in self.subjects:
            del self.subjects[name_clean]
            self.updated_at = datetime.now().isoformat()
            return True
        return False

    def update_attendance(self, attended: int, total: int) -> None:
        """Update attendance metrics."""
        if total < 0 or attended < 0:
            raise ValueError("Attendance numbers cannot be negative.")
        if attended > total:
            raise ValueError("Attended classes cannot exceed total classes.")
        self.attendance = AttendanceRecord(
            total_classes=total,
            attended_classes=attended,
        )
        self.updated_at = datetime.now().isoformat()

    def record_fee_payment(self, amount: float) -> None:
        """Record a fee payment."""
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        self.fees.paid_amount = min(
            self.fees.total_fee,
            round(self.fees.paid_amount + amount, 2)
        )
        self.updated_at = datetime.now().isoformat()

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        """Convert Student to JSON-serializable dictionary."""
        return {
            "roll_number": self.roll_number,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "course": self.course,
            "semester": self.semester,
            "subjects": {k: v.to_dict() for k, v in self.subjects.items()},
            "attendance": self.attendance.to_dict(),
            "fees": self.fees.to_dict(),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            # Legacy field for full backward compatibility
            "roll": self.roll_number,
            "marks": self.overall_percentage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Student:
        """
        Create a Student instance from a dictionary.
        Supports both legacy schema ({"roll": "...", "name": "...", "marks": ...})
        and the full professional schema.
        """
        roll = str(data.get("roll_number") or data.get("roll") or "").strip()
        name = str(data.get("name", "")).strip()

        # Handle subjects
        subjects_dict: Dict[str, SubjectScore] = {}
        if "subjects" in data and isinstance(data["subjects"], dict):
            for sub_name, sub_data in data["subjects"].items():
                if isinstance(sub_data, dict):
                    subjects_dict[sub_name] = SubjectScore.from_dict(sub_data)
                elif isinstance(sub_data, (int, float)):
                    subjects_dict[sub_name] = SubjectScore(
                        subject_name=sub_name,
                        marks_obtained=float(sub_data),
                        max_marks=100.0,
                    )
        elif "marks" in data and isinstance(data["marks"], (int, float)):
            # Legacy single mark fallback
            subjects_dict["General Studies"] = SubjectScore(
                subject_name="General Studies",
                marks_obtained=float(data["marks"]),
                max_marks=100.0,
            )

        # Handle attendance
        if "attendance" in data and isinstance(data["attendance"], dict):
            attendance = AttendanceRecord.from_dict(data["attendance"])
        else:
            attendance = AttendanceRecord()

        # Handle fees
        if "fees" in data and isinstance(data["fees"], dict):
            fees = FeeRecord.from_dict(data["fees"])
        else:
            fees = FeeRecord()

        return cls(
            roll_number=roll,
            name=name,
            email=str(data.get("email", "")),
            phone=str(data.get("phone", "")),
            course=str(data.get("course", "Computer Science")),
            semester=int(data.get("semester", 1)),
            subjects=subjects_dict,
            attendance=attendance,
            fees=fees,
            status=str(data.get("status", "ACTIVE")).upper(),
            created_at=str(data.get("created_at", datetime.now().isoformat())),
            updated_at=str(data.get("updated_at", datetime.now().isoformat())),
        )

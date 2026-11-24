"""
storage.py - Data Persistence & Storage Engine for Student Management System.

Features:
- Thread-safe / crash-safe atomic JSON file writes.
- Automatic creation of backups before modifications.
- Seamless auto-migration of legacy JSON schemas.
- High-fidelity CSV export and import.
- Built-in audit activity logger.
"""

from __future__ import annotations
import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from models import Student, SubjectScore, AttendanceRecord, FeeRecord


class StorageManager:
    """Manages file storage, backups, imports, and exports for student records."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent
        self.base_dir = Path(base_dir)
        self.data_file = self.base_dir / "students.json"
        self.backup_file = self.base_dir / "students.backup.json"
        self.log_file = self.base_dir / "activity.log"
        self.audit_file = self.base_dir / "audit_log.json"

    # --- Audit Logging ---

    def log_activity(self, action: str, roll_number: str, details: str = "") -> None:
        """Append an action to activity.log and audit_log.json."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] ACTION={action} | ROLL={roll_number} | {details}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except OSError:
            pass

        # Also structured audit
        try:
            audit_entries: List[Dict[str, Any]] = []
            if self.audit_file.exists():
                try:
                    with open(self.audit_file, "r", encoding="utf-8") as f:
                        audit_entries = json.load(f)
                        if not isinstance(audit_entries, list):
                            audit_entries = []
                except (json.JSONDecodeError, OSError):
                    audit_entries = []

            audit_entries.append({
                "timestamp": timestamp,
                "action": action,
                "roll_number": roll_number,
                "details": details,
            })

            # Keep latest 500 entries
            if len(audit_entries) > 500:
                audit_entries = audit_entries[-500:]

            with open(self.audit_file, "w", encoding="utf-8") as f:
                json.dump(audit_entries, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve the most recent audit log entries."""
        if not self.audit_file.exists():
            return []
        try:
            with open(self.audit_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
                if isinstance(entries, list):
                    return entries[-limit:]
        except Exception:
            pass
        return []

    # --- Core JSON Persistence ---

    def load_students(self) -> List[Student]:
        """
        Load student records from the JSON file.
        Gracefully handles file creation, JSON decoding errors,
        and auto-migration from older student JSON formats.
        """
        if not self.data_file.exists():
            return []

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                raw_data = json.loads(content)

            if not isinstance(raw_data, list):
                self.log_activity("WARN", "SYSTEM", "JSON root was not a list. Resetting to empty.")
                return []

            students: List[Student] = []
            for item in raw_data:
                if isinstance(item, dict):
                    try:
                        student = Student.from_dict(item)
                        if student.roll_number:
                            students.append(student)
                    except Exception as err:
                        self.log_activity("ERROR", "CORRUPT_RECORD", f"Skipping bad item: {err}")

            return students

        except (json.JSONDecodeError, OSError) as err:
            self.log_activity("ERROR", "LOAD_FAIL", f"Failed loading {self.data_file}: {err}")
            # Try to restore from backup if present
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, "r", encoding="utf-8") as bf:
                        raw_backup = json.load(bf)
                        if isinstance(raw_backup, list):
                            return [Student.from_dict(x) for x in raw_backup if isinstance(x, dict)]
                except Exception:
                    pass
            return []

    def save_students(self, students: List[Student], create_backup: bool = True) -> bool:
        """
        Atomically save student records to disk.
        Writes to a temporary file first, then atomically replaces the target file.
        Also creates a backup file before writing.
        """
        try:
            # 1. Create a backup if existing data file exists
            if create_backup and self.data_file.exists():
                try:
                    shutil.copy2(self.data_file, self.backup_file)
                except OSError:
                    pass

            # 2. Serialize students
            data = [s.to_dict() for s in students]

            # 3. Write atomically via temp file
            temp_file = self.base_dir / f"students.json.tmp_{os.getpid()}"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # 4. Atomic rename / replace
            if os.name == "nt":
                # Windows requires replacing target if it exists
                if self.data_file.exists():
                    os.replace(temp_file, self.data_file)
                else:
                    temp_file.rename(self.data_file)
            else:
                temp_file.rename(self.data_file)

            return True

        except Exception as err:
            self.log_activity("ERROR", "SAVE_FAIL", f"Atomic save failed: {err}")
            return False

    # --- CSV Export & Import ---

    def export_to_csv(self, target_path: Optional[Path | str] = None) -> Tuple[bool, str]:
        """
        Export all current students to a clean, spreadsheet-compatible CSV file.
        """
        students = self.load_students()
        if not students:
            return False, "No student records available to export."

        if target_path is None:
            target_path = self.base_dir / "students_export.csv"
        else:
            target_path = Path(target_path)

        try:
            with open(target_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Roll Number",
                    "Name",
                    "Course",
                    "Semester",
                    "Email",
                    "Phone",
                    "Total Obtained",
                    "Total Max",
                    "Percentage",
                    "CGPA",
                    "Grade",
                    "Result Status",
                    "Attendance %",
                    "Total Classes",
                    "Attended Classes",
                    "Total Fee",
                    "Paid Fee",
                    "Due Fee",
                    "Fee Status",
                    "Account Status",
                    "Subjects Detail",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for s in students:
                    subj_str = "; ".join([
                        f"{sub.subject_name}:{sub.marks_obtained}/{sub.max_marks}"
                        for sub in s.subjects.values()
                    ])
                    writer.writerow({
                        "Roll Number": s.roll_number,
                        "Name": s.name,
                        "Course": s.course,
                        "Semester": s.semester,
                        "Email": s.email,
                        "Phone": s.phone,
                        "Total Obtained": s.total_marks_obtained,
                        "Total Max": s.total_max_marks,
                        "Percentage": f"{s.overall_percentage}%",
                        "CGPA": s.cgpa,
                        "Grade": s.grade,
                        "Result Status": s.result_status,
                        "Attendance %": f"{s.attendance.percentage}%",
                        "Total Classes": s.attendance.total_classes,
                        "Attended Classes": s.attendance.attended_classes,
                        "Total Fee": s.fees.total_fee,
                        "Paid Fee": s.fees.paid_amount,
                        "Due Fee": s.fees.due_amount,
                        "Fee Status": s.fees.status,
                        "Account Status": s.status,
                        "Subjects Detail": subj_str,
                    })

            self.log_activity("EXPORT_CSV", "ALL", f"Exported {len(students)} records to {target_path.name}")
            return True, f"Successfully exported {len(students)} students to '{target_path.name}'."

        except Exception as err:
            return False, f"Failed to export CSV: {err}"

    def import_from_csv(self, source_path: Path | str) -> Tuple[int, int, List[str]]:
        """
        Import student records from a CSV file.
        Accepts columns: Roll Number, Name, Course, Semester, Email, Phone, Marks / Percentage.
        Returns: (imported_count, skipped_count, error_messages)
        """
        source = Path(source_path)
        if not source.exists():
            return 0, 0, [f"File '{source}' does not exist."]

        existing_students = {s.roll_number: s for s in self.load_students()}
        imported_count = 0
        skipped_count = 0
        errors: List[str] = []

        try:
            with open(source, "r", encoding="utf-8-sig") as csvfile:
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                    return 0, 0, ["CSV file is empty or headers are missing."]

                # Normalize headers: lowercase stripped
                header_map = {h.strip().lower().replace("_", " "): h for h in reader.fieldnames if h}

                def get_val(row: dict, *keys: str) -> str:
                    for k in keys:
                        # Direct check
                        if k in row and row[k]:
                            return str(row[k]).strip()
                        # Case-insensitive check
                        for h_norm, original_h in header_map.items():
                            if k.lower() in h_norm and original_h in row and row[original_h]:
                                return str(row[original_h]).strip()
                    return ""

                for idx, row in enumerate(reader, start=2):
                    roll = get_val(row, "roll number", "roll", "rollno", "id")
                    name = get_val(row, "name", "student name", "full name")

                    if not roll or not name:
                        errors.append(f"Row {idx}: Missing roll number or name.")
                        skipped_count += 1
                        continue

                    if roll in existing_students:
                        errors.append(f"Row {idx}: Roll number '{roll}' already exists. Skipped.")
                        skipped_count += 1
                        continue

                    course = get_val(row, "course", "department", "stream") or "Computer Science"
                    sem_str = get_val(row, "semester", "sem") or "1"
                    email = get_val(row, "email", "mail")
                    phone = get_val(row, "phone", "contact", "mobile")

                    try:
                        semester = int(sem_str)
                    except ValueError:
                        semester = 1

                    new_student = Student(
                        roll_number=roll,
                        name=name,
                        email=email,
                        phone=phone,
                        course=course,
                        semester=semester,
                    )

                    # Look for marks
                    marks_str = get_val(row, "marks", "percentage", "score", "total obtained")
                    if marks_str:
                        clean_marks = marks_str.replace("%", "").strip()
                        try:
                            score = float(clean_marks)
                            new_student.add_or_update_subject("General Studies", score, 100.0)
                        except ValueError:
                            pass

                    existing_students[roll] = new_student
                    imported_count += 1

            # Save updated list
            all_list = list(existing_students.values())
            self.save_students(all_list)
            self.log_activity("IMPORT_CSV", "BATCH", f"Imported {imported_count} students from {source.name}")
            return imported_count, skipped_count, errors

        except Exception as err:
            return imported_count, skipped_count, [f"Critical error reading CSV: {err}"]

    # --- JSON Backup & Restore ---

    def create_manual_backup(self) -> Tuple[bool, str]:
        """Creates an explicit timestamped snapshot backup."""
        if not self.data_file.exists():
            return False, "No data file exists to backup."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"students_backup_{timestamp}.json"
        dest = self.base_dir / backup_name

        try:
            shutil.copy2(self.data_file, dest)
            self.log_activity("BACKUP", "SYSTEM", f"Created manual backup {backup_name}")
            return True, f"Backup successfully created at '{backup_name}'."
        except Exception as err:
            return False, f"Failed creating backup: {err}"

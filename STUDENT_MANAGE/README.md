# 🎓 Student Management & Academic Information System (SMS)
*Enterprise Academic Records, Performance Analytics & Transcript Management Platform*

---

## 🌟 Overview
The **Student Management System** is a production-grade, modular, and terminal-based academic management suite developed in Python. It provides institutional-grade administration for student enrollments, multi-subject grade evaluations, cumulative GPA tracking, lecture attendance monitoring, tuition fee accounting, and merit rankings.

Built entirely with the Python Standard Library (zero external dependencies required), the system features high-fidelity ANSI color styling, dynamic Unicode box-drawing tables, crash-proof atomic JSON storage, automated backups, and instant CSV/JSON data export/import.

---

## ✨ Key Features

### 📋 1. Comprehensive Student Directory
- Multi-column Unicode tables displaying Roll Number, Full Name, Department/Course, Current Semester, Marks Percentage, CGPA, Letter Grade, Attendance %, Fee Status, and Enrollment Status.
- Natural sorting and instant ordering by:
  - Roll Number (Natural numeric ordering)
  - Full Name (Alphabetical A–Z)
  - Overall Percentage / CGPA (High to Low)
  - Attendance Health (%)
  - Course / Branch

### ➕ 2. Guided Student Enrollment
- Strict validation ensuring no duplicate roll numbers.
- Captures personal details (Name, Contact Number, Email, Branch, Semester).
- Allows immediate entry of course subjects and marks or quick enrollment.
- Initializes attendance metrics and tuition fee schedules.

### 🔍 3. Intelligent Universal Search
- Case-insensitive substring query across:
  - Roll Number (e.g. `2504650100008` or `101`)
  - Student Name (e.g. `Chandan`, `Rahul`)
  - Department / Stream (e.g. `Computer Science`, `Mechanical`)
  - Letter Grade (e.g. `A+`, `A`, `B`)
- One-click shortcut to inspect the student's complete academic transcript.

### 📝 4. Multi-Subject Academic Evaluation & CGPA Engine
- Multiple subjects per student with custom maximum and obtained scores.
- Dynamic auto-computation of:
  - Total Marks Obtained vs Maximum Marks
  - Overall Percentage
  - Standard 10.0 scale CGPA ($Percentage / 9.5$)
  - Letter Grade assignment:
    - **A+** : $\ge 90\%$
    - **A** : $80\% - 89.9\%$
    - **B+** : $70\% - 79.9\%$
    - **B** : $60\% - 69.9\%$
    - **C** : $50\% - 59.9\%$
    - **D** : $40\% - 49.9\%$
    - **F** : $< 40\%$ (Fail / Arrear)
  - Academic Classification: *Distinction*, *First Class*, *Second Class*, *Passed*, or *Failed*.

### 📅 5. Attendance & Tuition Fee Administration
- Real-time attendance percentage tracking with color-coded alerts.
- Automatic **Attendance Shortage Warning** for students with $< 75\%$ attendance, calculating exactly how many consecutive lectures they must attend to regain eligibility.
- Tuition fee ledger calculating Total Fee, Paid Amount, Pending Dues, and status (`PAID`, `PARTIAL`, `PENDING`).

### 📜 6. Official Academic Transcript & Report Card
- Generates a beautifully formatted, printable ASCII Marksheet & Transcript:
  - Institutional header and accreditation details
  - Student academic information box
  - Detailed subject-by-subject evaluation table with pass/fail marks
  - Final CGPA, Overall Percentage, and Letter Grade
  - Visual attendance progress bar (`[████████░░] 85.0%`)
  - Verification seal and Dean / Controller of Examinations signature blocks
  - Option to export the transcript to an individual text file (`transcript_<roll>.txt`).

### 🏆 7. Merit Rankings & Class Leaderboard
- Class Topper gold medalist highlight.
- Top 10 rankings with medal badges (🥇 1st, 🥈 2nd, 🥉 3rd).
- Proper tie handling for identical percentages.

### 📈 8. Institutional Analytics & Grade Histogram
- Class statistics: Total students, pass rate, average score, high/low scores.
- Subject-by-subject evaluation benchmarks: Enrolled count, average score, maximum/minimum scores, and pass rate.
- ASCII terminal bar chart histogram displaying the distribution of letter grades.

### 💾 9. Enterprise Data Storage & Archival
- **Atomic File Writes**: Prevents file corruption during unexpected system power loss or process kill.
- **Automatic Snapshot Backups**: Creates `students.backup.json` before saving modifications.
- **Manual Backups**: Instant timestamped backup creation (`students_backup_YYYYMMDD_HHMMSS.json`).
- **CSV Export & Import**: Full compatibility with Microsoft Excel, Google Sheets, and LibreOffice Calc.
- **Audit Logging**: Keeps an immutable trail of actions (`ADD_STUDENT`, `UPDATE_MARKS`, `FEE_PAYMENT`, `DELETE_STUDENT`) with timestamps in `activity.log` and `audit_log.json`.

---

## 🏗️ Project Architecture

```
Student_Management/
│
├── main.py                    # Interactive CLI application & menu navigation
├── student.py                 # Backward-compatible API for legacy scripts
├── models.py                  # Domain models (Student, SubjectScore, Attendance, Fees)
├── storage.py                 # Storage engine (Atomic saves, backups, CSV/JSON, Audit log)
├── manager.py                 # Business logic, query engine, leaderboard & analytics
├── ui.py                      # ANSI Terminal colors, Unicode tables, charts & transcripts
├── test_student_management.py # Automated unit test suite (16 comprehensive tests)
├── students.json              # Persistent database with preloaded student records
└── README.md                  # Complete technical and user documentation
```

---

## 🚀 How to Run

### Run the Main Application
Open PowerShell or your terminal in this directory and execute:

```powershell
python main.py
```

### Run the Automated Unit Tests
To verify all models, persistence logic, calculations, and analytics:

```powershell
python -m unittest discover -s .
```

### Run via Legacy Script / Module
If you have an existing script importing `student`:

```python
import student

students = student.load_students()
student.view_students(students)
```

---

## 👥 Preloaded Sample Records
The system comes preloaded with realistic student records:
- **Chandan Rao** (Roll: `2504650100008`) - B.Tech Computer Science (Sem-4) - CGPA: 9.68 (Class Topper 🥇)
- **Rahul Kumar** (Roll: `101`) - B.Tech Computer Science (Sem-4)
- **Aman Kumar** (Roll: `102`) - B.Tech Computer Science (Sem-4)
- **Priya Kumari** (Roll: `103`) - B.Tech Information Technology (Sem-4)
- **Neha Kumari** (Roll: `104`) - B.Tech Computer Science (Sem-4) - Attendance Alert (<75%)
- **Rohit Kumar** (Roll: `105`) - B.Tech Mechanical Engineering (Sem-4)
- **Anjali Sharma** (Roll: `106`) - BCA (Sem-2)

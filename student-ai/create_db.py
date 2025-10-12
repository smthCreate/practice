import sqlite3

conn = sqlite3.connect("school.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    full_name TEXT,
    grade_level INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS academic_records (
    record_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    subject TEXT,
    week_number INTEGER,
    grade REAL,
    attendance INTEGER,          -- 1 = был, 0 = пропустил
    absence_reason TEXT,
    club_attended INTEGER,
    event TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
)
""")

conn.commit()
conn.close()
print("✅ БД school.db создана!")
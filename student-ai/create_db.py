import sqlite3
import os

# Удаление старой базы данных (если существует)
if os.path.exists("school.db"):
    os.remove("school.db")
    print("✅ Старый файл базы данных удален.")

# Создание новой базы данных
conn = sqlite3.connect("school.db")
cur = conn.cursor()

# Таблица для студентов
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    full_name TEXT,
    grade_level INTEGER
)
""")

# Таблица для посещаемости (attendance)
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    record_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    subject TEXT,
    week_number INTEGER,
    day_number INTEGER,           -- Номер дня недели (1-5)
    attended INTEGER,             -- 1 = был, 0 = пропустил
    absence_reason TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
)
""")

# Таблица для оценок по предметам (grades)
cur.execute("""
CREATE TABLE IF NOT EXISTS grades (
    record_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    subject TEXT,
    week_number INTEGER,
    day_number INTEGER,           -- Номер дня недели (1-5)
    grade REAL,                   -- Оценка за день
    FOREIGN KEY(student_id) REFERENCES students(student_id)
)
""")

# Таблица для кружков и мероприятий (clubs_events)
cur.execute("""
CREATE TABLE IF NOT EXISTS clubs_events (
    record_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    week_number INTEGER,
    day_number INTEGER,           -- Номер дня недели (1-5)
    club TEXT,
    event TEXT,
    club_intensity REAL,          -- Интенсивность кружка
    total_club_hours INTEGER,     -- Часы, потраченные на кружки
    FOREIGN KEY(student_id) REFERENCES students(student_id)
)
""")

# Подтверждение изменений и закрытие соединения
conn.commit()
conn.close()
print("✅ БД school.db создана с обновленной структурой!")
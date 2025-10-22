import sqlite3
import pandas as pd
import numpy as np
from faker import Faker
import random
from tqdm import tqdm

# === Настройки ===
NUM_STUDENTS = 5000
WEEKS_PER_STUDENT = 20
SUBJECTS = ["math", "russian", "physics", "literature", "biology"]
EVENTS = [None, "olympiad", "competition", "camp", "illness"]
ABSENCE_REASONS = [None, "illness", "competition", "family", "other"]
CLUB_TYPES = ["science", "arts", "sports", "none"]

fake = Faker("ru_RU")
Faker.seed(42)
np.random.seed(42)

# === Генерация учеников ===
students = []
for i in range(1, NUM_STUDENTS + 1):
    students.append({
        "student_id": i,
        "full_name": fake.name(),
        "grade_level": np.random.randint(7, 12)
    })

# === Генерация академических записей ===
attendance_records = []
grade_records = []
club_event_records = []

for student in tqdm(students, desc="Генерация данных"):
    student_id = student["student_id"]
    grade_level = student["grade_level"]
    
    # Базовый "уровень" ученика (от 2.5 до 5.0)
    base_skill = np.clip(np.random.normal(4.0, 0.6), 2.5, 5.0)
    
    for week in range(1, WEEKS_PER_STUDENT + 1):
        for subject in SUBJECTS:
            # Случайное событие
            event = np.random.choice(EVENTS, p=[0.7, 0.08, 0.07, 0.05, 0.1])
            
            # Причина пропуска
            absence_reason = None
            attendance = 1
            
            if event == "illness":
                absence_reason = "illness"
                attendance = 0
            elif event in ["competition", "camp"]:
                absence_reason = event
                attendance = np.random.choice([0, 1], p=[0.6, 0.4])
            else:
                # Обычный пропуск
                if np.random.rand() < 0.08:
                    absence_reason = np.random.choice(["family", "other"])
                    attendance = 0
            
            # Посещение кружка
            club_attended = int(np.random.rand() > 0.4)
            
            # Моделируем оценку
            grade_noise = np.random.normal(0, 0.4)
            grade_trend = 0
            
            # Влияние событий
            if event == "olympiad" and subject in ["math", "physics"]:
                grade_trend += 0.4
            if event == "illness":
                grade_trend -= 0.5
            if club_attended and subject in ["math", "physics", "literature"]:
                grade_trend += 0.2
            
            # Постепенное снижение/рост (для реалистичности)
            drift = (week - 10) * np.random.normal(0, 0.02)
            
            grade = base_skill + grade_trend + grade_noise + drift
            grade = np.clip(round(grade * 2) / 2, 2.0, 5.0)  # только с шагом 0.5
            
            # Создание записей для таблиц
            attendance_records.append({
                "student_id": student_id,
                "subject": subject,
                "week_number": week,
                "day_number": random.randint(1, 5),  # случайный день недели
                "attended": attendance,
                "absence_reason": absence_reason
            })

            grade_records.append({
                "student_id": student_id,
                "subject": subject,
                "week_number": week,
                "day_number": random.randint(1, 5),
                "grade": grade
            })
            
            club_event_records.append({
                "student_id": student_id,
                "week_number": week,
                "day_number": random.randint(1, 5),
                "club": np.random.choice(CLUB_TYPES),
                "event": event,
                "club_intensity": np.random.uniform(0.5, 1.5),  # случайная интенсивность
                "total_club_hours": random.randint(1, 3)
            })

# === Преобразуем в DataFrame ===
df_attendance = pd.DataFrame(attendance_records)
df_grades = pd.DataFrame(grade_records)
df_clubs_events = pd.DataFrame(club_event_records)

# === Сохраняем в SQLite ===
conn = sqlite3.connect("school_main.db")

# Сохраняем студентов
pd.DataFrame(students).to_sql("students", conn, if_exists="append", index=False)

# Сохраняем записи с посещаемостью
df_attendance.to_sql("attendance", conn, if_exists="append", index=False)

# Сохраняем записи с оценками
df_grades.to_sql("grades", conn, if_exists="append", index=False)

# Сохраняем записи с кружками и мероприятиями
df_clubs_events.to_sql("clubs_events", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"✅ Сгенерировано {len(df_attendance)} записей для посещаемости, {len(df_grades)} записей для оценок и {len(df_clubs_events)} записей для кружков.")

import random
import numpy as np
import pandas as pd
from faker import Faker
import sqlite3

# === Настройки ===
NUM_STUDENTS = 500
WEEKS_PER_STUDENT = 20
DAYS_IN_WEEK = 5  # Рабочие дни в неделе
SUBJECTS = ["math", "russian", "physics", "literature", "biology"]
CLUBS = ["science", "arts", "sports", "none"]  # Разные кружки
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

# === Создаем списки для каждой таблицы ===
attendance_records = []
grade_records = []
club_event_records = []

for student in students:
    student_id = student["student_id"]
    
    # Генерация кружков для каждого ученика
    student_clubs = random.sample(CLUBS, random.randint(1, 3))  # Дети могут посещать от 1 до 3 кружков
    total_club_hours = sum([random.randint(1, 3) for club in student_clubs])  # 1-3 часа в неделю на кружок
    club_intensity = sum([1 if club == "sports" else 0.5 for club in student_clubs])  # Спортивные кружки тяжелее

    # Фиксированное расписание уроков на первую неделю
    weekly_schedule = {day: random.sample(SUBJECTS, 3) for day in range(1, DAYS_IN_WEEK + 1)}  # 3 предмета в день

    # Генерация записей по каждому дню для каждого ученика
    for week in range(1, WEEKS_PER_STUDENT + 1):
        for day in range(1, DAYS_IN_WEEK + 1):  # Перебираем каждый день недели
            # Таблица посещаемости (attendance)
            for subject in weekly_schedule[day]:  # Прочитаем предметы для этого дня
                subject_attended = np.random.choice([0, 1], p=[0.2, 0.8])  # Вероятность посещения предмета (80% посещаемость)
                attendance_records.append({
                    "student_id": student_id,
                    "subject": subject,
                    "week_number": week,
                    "day_number": day,
                    "attended": subject_attended,  # Был ли на уроке
                    "absence_reason": "illness" if subject_attended == 0 else None  # Пропуск по болезни (если не был)
                })

            # Таблица оценок (grades)
            for subject in weekly_schedule[day]:
                grade_noise = np.random.normal(0, 0.4)
                grade = np.clip(np.random.normal(4.0, 0.6) + grade_noise, 2.0, 5.0)  # Оценка
                grade_records.append({
                    "student_id": student_id,
                    "subject": subject,
                    "week_number": week,
                    "day_number": day,
                    "grade": grade  # Оценка за день
                })

            # Таблица кружков и мероприятий (clubs_events)
            for club in student_clubs:
                event = "olympiad" if random.random() > 0.8 else "competition"  # Случайные мероприятия
                club_event_records.append({
                    "student_id": student_id,
                    "week_number": week,
                    "day_number": day,
                    "club": club,
                    "event": event,
                    "club_intensity": club_intensity,
                    "total_club_hours": total_club_hours
                })

# === Преобразуем в DataFrame ===
df_attendance = pd.DataFrame(attendance_records)
df_grades = pd.DataFrame(grade_records)
df_clubs_events = pd.DataFrame(club_event_records)

# === Сохраняем в SQLite ===
conn = sqlite3.connect("school.db")

df_attendance.to_sql("attendance", conn, if_exists="replace", index=False)
df_grades.to_sql("grades", conn, if_exists="replace", index=False)
df_clubs_events.to_sql("clubs_events", conn, if_exists="replace", index=False)

conn.close()

print(f"✅ Сгенерировано {len(df_attendance)} записей для посещаемости, {len(df_grades)} записей для оценок, {len(df_clubs_events)} записей для кружков.")

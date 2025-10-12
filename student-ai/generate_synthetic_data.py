# generate_synthetic_data.py
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
records = []

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
            
            records.append({
                "student_id": student_id,
                "subject": subject,
                "week_number": week,
                "grade": grade,
                "attendance": attendance,
                "absence_reason": absence_reason,
                "club_attended": club_attended,
                "event": event
            })

# === Преобразуем в DataFrame ===
df_records = pd.DataFrame(records)

# === Добавляем целевую переменную (target) ===
# Цель: предсказать, упадёт ли средний балл за последние 2 недели по сравнению с предыдущими 4

def compute_target(group):
    group = group.sort_values("week_number")
    grades = group["grade"].values
    weeks = group["week_number"].values
    
    target = np.zeros(len(grades))
    # Начинаем с 6-й недели (чтобы было 4+2 окно)
    for i in range(5, len(grades)):
        # последние 2 недели
        recent_avg = grades[i-1:i+1].mean()
        # предыдущие 4 недели
        past_avg = grades[i-5:i-1].mean()
        # если упало более чем на 0.3 балла
        if past_avg - recent_avg > 0.3:
            target[i] = 1
    group["target"] = target
    return group

print("Вычисление целевой переменной...")
df_with_target = df_records.groupby(["student_id", "subject"]).apply(compute_target).reset_index(drop=True)

# === Сохраняем в SQLite ===
conn = sqlite3.connect("school.db")

# Сохраняем студентов
pd.DataFrame(students).to_sql("students", conn, if_exists="replace", index=False)

# Сохраняем записи с таргетом
df_with_target.to_sql("academic_records", conn, if_exists="replace", index=False)

conn.close()

print(f"✅ Сгенерировано {len(df_with_target)} записей для {NUM_STUDENTS} учеников.")
print(f"📊 Распределение target: {df_with_target['target'].value_counts().to_dict()}")
import sqlite3
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

# === Константы ===
SUBJECT_TO_ID = {
    "math": 0,
    "russian": 1,
    "physics": 2,
    "literature": 3,
    "biology": 4
}
REASON_TO_ID = {
    None: 0,
    "illness": 1,
    "competition": 2,
    "family": 3,
    "other": 4,
    "camp": 5
}

CLUB_TO_ID = {
    "science": 0,
    "arts": 1,
    "sports": 2,
    "none": 3
}

def load_samples(db_path="school.db", seq_len=8, split="train", test_ratio=0.2):
    """
    Вспомогательная функция: загружает сырые последовательности (список словарей).
    """
    conn = sqlite3.connect(db_path)

    # Загрузка посещаемости (attendance)
    attendance_df = pd.read_sql_query("""
        SELECT student_id, subject, week_number, day_number, attended, absence_reason
        FROM attendance
        ORDER BY student_id, subject, week_number, day_number
    """, conn)
    
    # Загрузка оценок (grades)
    grades_df = pd.read_sql_query("""
        SELECT student_id, subject, week_number, day_number, grade
        FROM grades
        ORDER BY student_id, subject, week_number, day_number
    """, conn)

    # Загрузка кружков и мероприятий (clubs_events)
    clubs_events_df = pd.read_sql_query("""
        SELECT student_id, week_number, day_number, club, event, club_intensity, total_club_hours
        FROM clubs_events
        ORDER BY student_id, week_number, day_number
    """, conn)

    conn.close()

    # Объединение данных
    df = pd.merge(attendance_df, grades_df, on=["student_id", "subject", "week_number", "day_number"], how="left")
    df = pd.merge(df, clubs_events_df, on=["student_id", "week_number", "day_number"], how="left")

    # Делим по student_id
    all_students = df['student_id'].unique()
    np.random.seed(42)
    np.random.shuffle(all_students)
    split_idx = int(len(all_students) * (1 - test_ratio))
    
    if split == "train":
        student_ids = set(all_students[:split_idx])
    else:  # "test"
        student_ids = set(all_students[split_idx:])
    
    df = df[df['student_id'].isin(student_ids)].copy()

    # Формируем последовательности
    samples = []
    grouped = df.groupby(['student_id', 'subject'])
    for (student_id, subject), group in grouped:
        if len(group) < seq_len + 1:
            continue
        group = group.sort_values('week_number').reset_index(drop=True)
        for i in range(len(group) - seq_len):
            window = group.iloc[i:i + seq_len]
            target = group.iloc[i + seq_len]['grade']  # Целевая переменная: оценка
            if pd.isna(target):
                continue

            # Нагрузка от кружков
            total_club_hours = window['total_club_hours'].sum()  # Суммируем участие в кружках за 8 недель
            club_intensity = window['club_intensity'].mean()  # Средняя интенсивность посещаемости кружков

            # Преобразуем названия кружков в числовые значения с использованием словаря
            samples.append({
                'subject': SUBJECT_TO_ID[subject],
                'absence': [REASON_TO_ID.get(r, REASON_TO_ID["other"]) for r in window['absence_reason'].fillna('other').values],
                'club': [CLUB_TO_ID.get(c, CLUB_TO_ID["none"]) for c in window['club'].fillna('none').values],  # Преобразуем с использованием словаря
                'numeric': np.stack([window['grade'].values, window['attended'].values], axis=1).astype(np.float32),
                'target': float(target),
                'total_club_hours': total_club_hours,
                'club_intensity': club_intensity
            })
    return samples


class StudentPerformanceDataset(Dataset):
    def __init__(self, db_path="school.db", seq_len=8, split="train", test_ratio=0.2):
        self.seq_len = seq_len
        self.samples = load_samples(db_path, seq_len, split, test_ratio)
        print(f"✅ Загружено {len(self.samples)} последовательностей ({split})")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return {
            "subject": torch.tensor(sample["subject"], dtype=torch.long).repeat(self.seq_len),
            "absence": torch.tensor(sample["absence"], dtype=torch.long),
            "club": torch.tensor(sample["club"], dtype=torch.long),
            "numeric": torch.tensor(sample["numeric"], dtype=torch.float32),
            "target": torch.tensor(sample["target"], dtype=torch.float32)
        }


def collate_fn(batch):
    return {
        "subject": torch.stack([item["subject"] for item in batch]),
        "absence": torch.stack([item["absence"] for item in batch]),
        "club": torch.stack([item["club"] for item in batch]),
        "numeric": torch.stack([item["numeric"] for item in batch]),
        "target": torch.stack([item["target"] for item in batch])
    }



# === Пример использования ===
# if __name__ == "__main__":
#     train_dataset = StudentPerformanceDataset(split="train")
#     test_dataset = StudentPerformanceDataset(split="test")
    
#     train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
#     test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)

#     print("\nПример батча из train:")
#     for batch in train_loader:
#         print("subject.shape:", batch["subject"].shape)
#         print("numeric.shape:", batch["numeric"].shape)
#         print("target.shape:", batch["target"].shape)
#         break
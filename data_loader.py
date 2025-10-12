# data_loader.py
import sqlite3
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from collections import defaultdict

# === Константы ===
SEQ_LEN = 8  # длина входной последовательности
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
    "camp": 5  # ← добавили
}
EVENT_TO_ID = {
    None: 0,
    "olympiad": 1,
    "competition": 2,
    "camp": 3,
    "illness": 4
}

class StudentPerformanceDataset(Dataset):
    def __init__(self, db_path="school.db", seq_len=8):
        self.seq_len = seq_len
        self.samples = []
        self._load_data(db_path)

    def _load_data(self, db_path):
        conn = sqlite3.connect(db_path)
        query = """
        SELECT student_id, subject, week_number, grade, attendance,
               absence_reason, club_attended, event, target
        FROM academic_records
        ORDER BY student_id, subject, week_number
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Группируем по (student_id, subject)
        grouped = df.groupby(['student_id', 'subject'])

        for (student_id, subject), group in grouped:
            if len(group) < self.seq_len + 1:
                continue  # пропускаем короткие истории

            # Сортируем по неделе (на всякий случай)
            group = group.sort_values('week_number').reset_index(drop=True)

            # Скользящее окно
            for i in range(len(group) - self.seq_len):
                window = group.iloc[i:i + self.seq_len]
                target = group.iloc[i + self.seq_len]['target']

                # Пропускаем, если target не определён (NaN)
                if pd.isna(target):
                    continue

                self.samples.append({
                    'subject': SUBJECT_TO_ID[subject],
                    'absence': [REASON_TO_ID[r] for r in window['absence_reason'].fillna('other').values],
                    'club': [int(c) for c in window['club_attended'].values],
                    'numeric': np.stack([
                        window['grade'].values,
                        window['attendance'].values,
                        window['club_attended'].values
                    ], axis=1).astype(np.float32),
                    'week': window['week_number'].values % 52,  # циклическая неделя
                    'target': float(target)
                })

        print(f"✅ Загружено {len(self.samples)} обучающих последовательностей")

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

# === Collate function для батчинга ===
def collate_fn(batch):
    return {
        "subject": torch.stack([item["subject"] for item in batch]),
        "absence": torch.stack([item["absence"] for item in batch]),
        "club": torch.stack([item["club"] for item in batch]),
        "numeric": torch.stack([item["numeric"] for item in batch]),
        "target": torch.stack([item["target"] for item in batch])
    }

# === Пример использования ===
if __name__ == "__main__":
    dataset = StudentPerformanceDataset(db_path="school.db", seq_len=SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)

    print("Пример батча:")
    for batch in dataloader:
        print("subject.shape:", batch["subject"].shape)      # [32, 8]
        print("numeric.shape:", batch["numeric"].shape)      # [32, 8, 3]
        print("target.shape:", batch["target"].shape)        # [32]
        break
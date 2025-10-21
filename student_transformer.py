import torch
import torch.nn as nn
import math

class StudentTransformer(nn.Module):
    def __init__(
        self,
        num_subjects=5,
        num_absence_reasons=6,
        num_club_types=2,
        numeric_features=2,
        embed_dim=64,
        num_heads=4,
        num_layers=2,
        dropout=0.1,
        max_seq_len=52,
        pred_type="binary"
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.pred_type = pred_type

        self.subject_embed = nn.Embedding(num_subjects, embed_dim)
        self.absence_embed = nn.Embedding(num_absence_reasons, embed_dim)
        self.club_embed = nn.Embedding(num_club_types, embed_dim)

        self.numeric_proj = nn.Linear(numeric_features, embed_dim)
        self.norm_numeric = nn.LayerNorm(embed_dim)

        self.pos_encoding = self._build_positional_encoding(max_seq_len, embed_dim)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        if pred_type == "binary":
            self.head = nn.Sequential(
                nn.Linear(embed_dim, 32),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(32, 1),
                nn.Sigmoid()
            )
        else:
            self.head = nn.Sequential(
                nn.Linear(embed_dim, 32),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(32, 1)
            )

    def _build_positional_encoding(self, max_len, d_model):
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        return pe.unsqueeze(0)

    def forward(self, x):
        B, L = x["subject"].shape
        # Проверка размерности перед числовым преобразованием
        print("Размерность x['numeric'] перед numeric_proj:", x["numeric"].shape)
        print(f"x['subject'].max(): {x['subject'].max()}")
        print(f"x['absence'].max(): {x['absence'].max()}")
        print(f"x['club'].max(): {x['club'].max()}")

        emb = (
            self.subject_embed(x["subject"]) +
            self.absence_embed(x["absence"]) +
            self.club_embed(x["club"]) +
            self.norm_numeric(self.numeric_proj(x["numeric"]))
        )
        emb = emb + self.pos_encoding[:, :L, :].to(emb.device)
        out = self.transformer(emb)
        last_out = out[:, -1, :]
        return self.head(last_out).squeeze(-1)


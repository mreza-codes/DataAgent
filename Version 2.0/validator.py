import pandas as pd
import re

class Validator:
    def __init__(self):
        pass

    def is_boolean_like(self, df, col):
        values = set(df[col].dropna().astype(str).str.lower().unique())
        return values <= {"true", "false", "0", "1"}

    def is_one_hot_group(self, df, col):
        prefix = col.split("_")[0]
        group = [c for c in df.columns if c.startswith(prefix + "_")]
        if len(group) >= 3:
            return all(self.is_boolean_like(df, c) for c in group)
        return False

    def can_delete(self, df, col):
        missing_ratio = df[col].isnull().mean()
        if missing_ratio > 0.85:
            return True
        if any(k in col.lower() for k in ["id", "index", "row_id"]):
            return True
        if df[col].nunique() <= 1:
            return True
        return False

    def can_encode(self, df, col):
        if self.is_boolean_like(df, col):
            return False
        if self.is_one_hot_group(df, col):
            return False
        if df[col].dtype not in ["object", "category"]:
            return False
        if df[col].nunique() > 30:
            return False
        return True

    def can_fill_missing(self, df, col):
        missing_ratio = df[col].isnull().mean()
        if missing_ratio == 0:
            return False
        if df[col].notnull().sum() < 5:
            return False
        if 0.05 < missing_ratio <= 0.85:
            return True
        return False

    def can_convert_type(self, df, col):
        if df[col].dtype != "object":
            return False
        numeric_test = pd.to_numeric(df[col], errors="coerce")
        if numeric_test.notnull().sum() > 0:
            return True
        datetime_test = pd.to_datetime(df[col], errors="coerce")
        if datetime_test.notnull().sum() > 0:
            return True
        return False

    def is_duration_column(self, df, col):
        sample = df[col].astype(str).head(20).str.lower()
        patterns = [
            r"\d+\s*min", r"\d+\s*season", r"\d+:\d+",
            r"pt\d+m", r"pt\d+h"
        ]
        for p in patterns:
            if sample.str.contains(p).any():
                return True
        return False

    def validate_step(self, df, step):
        action = step.get("action")
        col = step.get("column")

        if col not in df.columns:
            return False

        action = action.lower()

        if action == "delete":
            return self.can_delete(df, col)

        if action == "encode":
            return self.can_encode(df, col)

        if action == "fill_missing":
            return self.can_fill_missing(df, col)

        if action == "convert_type":
            return self.can_convert_type(df, col)

        if action == "convert_duration":
            return self.is_duration_column(df, col)

        if action == "skip":
            return True

        return False

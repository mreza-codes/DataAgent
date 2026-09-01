import pandas as pd
import numpy as np
import os
import requests
import json
from sklearn.preprocessing import LabelEncoder




class DataAgent:
    def __init__(self,model):
        self.model = model
        self.data = None
        self.plan = None
        self.cleaned_data = None
        self.charts = {}
        self.report = None  


    def call_model(self, prompt):
        return self.model(prompt)


    def load_file(self, file_path):
        """Load dataset from CSV/Excel/JSON"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            self.data = pd.read_csv(file_path)
        elif ext in [".xlsx",".xls"]:
            self.data = pd.read_excel(file_path)
        elif ext == ".json":
            self.data = pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file type")
        return True
            
        

    def preview(self):
        """Return basic info about dataset"""

        if self.data is None:
            raise ValueError("No dataset loaded")
        info = {
            "rows" : len(self.data),
            "columns" : len(self.data.columns),
            "null_counts" : self.data.isnull().sum().to_dict(),
            "dtypes" : self.data.dtypes.astype(str).to_dict(),
            "head" : self.data.head().to_dict(orient="records")
        }
        return info
        

    def reason(self):
        """Use model ONLY to detect column types and basic cleaning hints."""

        preview = self.preview()

        prompt = (
            "You are a professional data-cleaning assistant.\n\n"
            "Your ONLY job is to analyze the dataset preview and output a JSON object "
            "describing the TYPE of each column.\n\n"
            "STRICT RULES:\n"
            "- Output MUST be a single JSON object.\n"
            "- NO markdown, NO code blocks, NO backticks.\n"
            "- NO explanations.\n"
            "- NO cleaning decisions (NO drop, NO scaling, NO encoding).\n"
            "- ONLY detect column types and basic properties.\n\n"
            "Your JSON MUST contain exactly these sections:\n\n"
            "1. column_types\n"
            "   - Keys: column names\n"
            "   - Values: one of [\"numeric\", \"categorical\", \"text\", \"datetime\", \"unknown\"]\n\n"
            "2.missing_value_summary\n"
            "   - Keys: column names\n"
            "   - Values: a FLOAT between 0 and 1 (example: 0.25)\n"
            "   - Fractions like 10/8807 are NOT allowed.\n\n"
            "3. high_cardinality_columns\n"
            "   - Keys: column names\n"
            "   - Values: {\"unique_count\": number}\n\n"
            "4. datetime_detection\n"
            "   - Keys: column names\n"
            "   - Values: {\"is_datetime\": true/false}\n\n"
            "FORMAT EXAMPLE (FOLLOW STRUCTURE ONLY):\n\n"
            "{\n"
            "    \"column_types\": {\n"
            "        \"Age\": \"numeric\",\n"
            "        \"Name\": \"text\",\n"
            "        \"Sex\": \"categorical\",\n"
            "        \"DateAdded\": \"datetime\"\n"
            "    },\n"
            "    \"missing_value_summary\": {\n"
            "        \"Age\": 0.12,\n"
            "        \"Name\": 0.00\n"
            "    },\n"
            "    \"high_cardinality_columns\": {\n"
            "        \"Title\": {\"unique_count\": 1200}\n"
            "    },\n"
            "    \"datetime_detection\": {\n"
            "        \"DateAdded\": {\"is_datetime\": true}\n"
            "    }\n"
            "}\n\n"
            "Dataset preview:\n"
            f"{preview}\n\n"
            "Return ONLY valid JSON."
        )

        raw_output = self.call_model(prompt)
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()

        print("RAW OUTPUT FROM MODEL:")
        print(raw_output)

        self.plan = json.loads(raw_output)
        return self.plan


    

    def clean_data(self):
        """
        Stable + semantic cleaning.
        Safe for all datasets, but smart for known column patterns.
        """

        df = self.data.copy()
        plan = self.plan

        col_types = plan.get("column_types", {})
        datetime_info = plan.get("datetime_detection", {})

        # ---------------------------------------------------------
        # 0) Local type inference (fix model mistakes)
        # ---------------------------------------------------------
        inferred_types = {}

        for col in df.columns:
            s = df[col]

            # Detect numeric columns
            try:
                numeric_s = pd.to_numeric(s.dropna(), errors="coerce")
                numeric_ratio = numeric_s.notna().sum() / max(len(s.dropna()), 1)
            except:
                numeric_ratio = 0

            unique_count = s.nunique(dropna=True)

            if numeric_ratio > 0.9:
                inferred_types[col] = "numeric"
            elif unique_count < 0.05 * len(s) and unique_count < 50:
                inferred_types[col] = "categorical"
            else:
                inferred_types[col] = "text"

        # Override model mistakes
        for col in df.columns:
            if col_types.get(col, "unknown") in ["unknown", "object"]:
                col_types[col] = inferred_types[col]

        # ---------------------------------------------------------
        # 1) Convert datetime columns (safe)
        # ---------------------------------------------------------
        for col, info in datetime_info.items():

            # Boolean format
            if isinstance(info, bool):
                if info:
                    try:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                        col_types[col] = "datetime"
                    except:
                        pass
                continue

            # Dictionary format
            if info.get("is_datetime"):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    col_types[col] = "datetime"
                except:
                    pass

        # ---------------------------------------------------------
        # 2) Semantic cleaning based on column names
        # ---------------------------------------------------------
        for col in df.columns:
            lower = col.lower()

            # duration: convert "90 min" → 90
            if "duration" in lower:
                try:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.extract(r"(\d+)", expand=False)
                        .astype(float)
                    )
                    col_types[col] = "numeric"
                except:
                    pass

            # long text columns
            if any(key in lower for key in ["description", "overview", "synopsis"]):
                col_types[col] = "text_long"

            # ticket-like columns (Titanic)
            if "ticket" in lower:
                col_types[col] = "text"

            # cabin-like columns (Titanic)
            if "cabin" in lower:
                col_types[col] = "categorical"

        # ---------------------------------------------------------
        # 3) Handle missing values (safe)
        # ---------------------------------------------------------
        for col in df.columns:
            col_type = col_types.get(col, "unknown")

            if df[col].isna().sum() == 0:
                continue

            try:
                if col_type == "numeric":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    df[col] = df[col].fillna(df[col].median())

                elif col_type == "categorical":
                    if df[col].mode().size > 0:
                        df[col] = df[col].fillna(df[col].mode()[0])
                    else:
                        df[col] = df[col].fillna("Unknown")

                elif col_type == "datetime":
                    df[col] = df[col].ffill()

                elif col_type in ["text", "text_long"]:
                    df[col] = df[col].fillna("")

                else:
                    df[col] = df[col].fillna("")

            except:
                pass

        # ---------------------------------------------------------
        # 4) Encode categorical columns (safe)
        # ---------------------------------------------------------
        from sklearn.preprocessing import LabelEncoder

        for col, col_type in col_types.items():
            if col_type == "categorical":
                try:
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                except:
                    pass

        # ---------------------------------------------------------
        # 5) Fix skewed numeric columns (VERY SAFE)
        # ---------------------------------------------------------
        skip_keywords = ["population", "area", "density", "percentage", "rank"]

        for col, col_type in col_types.items():
            if col_type == "numeric":
                lower = col.lower()
                if any(key in lower for key in skip_keywords):
                    continue

                try:
                    if df[col].skew() > 1:
                        df[col] = np.log1p(df[col])
                except:
                    pass

        # ---------------------------------------------------------
        # 6) Drop columns that are 100% empty
        # ---------------------------------------------------------
        for col in df.columns:
            if df[col].isna().sum() == len(df):
                df = df.drop(columns=[col])

        self.cleaned_data = df
        return df








    def export_outputs(self, output_dir="outputs"):
        """Save cleaned CSV only."""

        if self.cleaned_data is None:
            raise ValueError("No cleaned data available")

        os.makedirs(output_dir, exist_ok=True)

        # فقط یک فایل دیتاست تمیز ذخیره می‌کنیم
        cleaned_path = os.path.join(output_dir, "cleaned_data.csv")
        self.cleaned_data.to_csv(cleaned_path, index=False)

        return True






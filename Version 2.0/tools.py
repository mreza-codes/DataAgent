import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import re

class Tools:
    def __init__(self):
        pass

    def delete_column(self, df, col):
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    def fill_missing_simple(self, df, col):
        if col not in df.columns:
            return
        df[col].fillna("Unknown", inplace=True)

    def encode_column(self, df, col):
        if col not in df.columns:
            return

        values = set(df[col].dropna().astype(str).str.lower().unique())
        if values <= {"true", "false", "0", "1"}:
            return

        prefix = col.split("_")[0]
        group = [c for c in df.columns if c.startswith(prefix + "_")]
        if len(group) >= 3:
            return

        encoded = pd.get_dummies(df[col], prefix=col)
        df.drop(columns=[col], inplace=True)
        df[encoded.columns] = encoded

    def convert_type(self, df, col, target_type):
        if col not in df.columns:
            return

        if target_type == "numeric":
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif target_type == "category":
            df[col] = df[col].astype("category")
        elif target_type == "datetime":
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif target_type == "string":
            df[col] = df[col].astype(str)

    def fill_missing_ml(self, df, col):
        if col not in df.columns:
            return

        y = df[col]
        not_null = y.notnull()

        X = df.drop(columns=[col]).copy()

        for c in X.columns:
            if X[c].dtype == "object":
                X[c] = pd.factorize(X[c].astype(str))[0]

        X = X.fillna(-1)

        model = (
            RandomForestClassifier(n_estimators=80)
            if y.dtype == "object"
            else RandomForestRegressor(n_estimators=120)
        )

        model.fit(X[not_null], y[not_null])
        df.loc[~not_null, col] = model.predict(X[~not_null])

    def convert_duration(self, df, col):
        if col not in df.columns:
            return

        minutes = []
        seasons = []

        for raw in df[col].astype(str).str.lower():
            if "min" in raw:
                nums = re.findall(r"\d+", raw)
                minutes.append(float(nums[0]) if nums else None)
                seasons.append(None)
            elif "season" in raw:
                nums = re.findall(r"\d+", raw)
                seasons.append(int(nums[0]) if nums else None)
                minutes.append(None)
            else:
                minutes.append(None)
                seasons.append(None)

        df[col + "_minutes"] = minutes
        df[col + "_seasons"] = seasons

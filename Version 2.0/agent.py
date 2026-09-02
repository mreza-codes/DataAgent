from validator import Validator
from tools import Tools
from deepseek_model import DeepSeekModel

class Agent:
    def __init__(self, model=None):
        self.validator = Validator()
        self.tools = Tools()
        self.model = model if model is not None else DeepSeekModel()
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    def create_preview(self, df):
        return {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_percent": df.isnull().mean().round(3).to_dict(),
            "sample_rows": df.head(5).to_dict(orient="records")
        }

    def generate_plan(self, df):
        preview = self.create_preview(df)
        plan = self.model.generate_cleaning_plan(preview)
        self.log("Generated cleaning plan.")
        return plan, preview

    def execute_plan(self, df, plan, preview):
        for step in plan:
            col = step.get("column")
            action = step.get("action")

            if col not in preview["columns"]:
                self.log(f"SKIPPED: Column '{col}' does not exist.")
                continue

            if not self.validator.validate_step(df, step):
                corrected = self.model.fix_step(step, preview)
                if not self.validator.validate_step(df, corrected):
                    self.log(f"INVALID STEP: {step}")
                    continue
                step = corrected

            self.run_step(df, step)

        return df

    def run_step(self, df, step):
        action = step.get("action")
        col = step.get("column")

        before_nulls = df[col].isnull().sum() if col in df.columns else None

        if action == "delete":
            self.tools.delete_column(df, col)
            self.log(f"DELETE: Column '{col}' removed.")

        elif action == "encode":
            self.tools.encode_column(df, col)
            self.log(f"ENCODE: Column '{col}' encoded into one-hot vectors.")

        elif action == "fill_missing":
            if df[col].dtype == "object":
                self.log(f"FILL_MISSING_SIMPLE: Filling missing values in '{col}' using simple strategy.")
                self.tools.fill_missing_simple(df, col)
            else:
                self.log(f"FILL_MISSING_ML: ML model imputing missing values for '{col}'.")
                self.tools.fill_missing_ml(df, col)

            after_nulls = df[col].isnull().sum()
            filled = before_nulls - after_nulls
            self.log(f" → Filled {filled} missing values in '{col}'.")

        elif action == "convert_type":
            self.tools.convert_type(df, col, "numeric")
            self.log(f"CONVERT_TYPE: Column '{col}' converted to numeric.")

        elif action == "convert_duration":
            self.tools.convert_duration(df, col)
            self.log(f"CONVERT_DURATION: Column '{col}' split into '{col}_minutes' and '{col}_seasons'.")

        elif action == "skip":
            self.log(f"SKIP: Column '{col}' left unchanged.")

    def clean_data(self, df):
        self.logs = []
        plan, preview = self.generate_plan(df)
        cleaned_df = self.execute_plan(df, plan, preview)
        self.log("CLEANING COMPLETE.")
        return cleaned_df, self.logs

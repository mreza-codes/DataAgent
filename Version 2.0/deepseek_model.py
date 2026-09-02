import requests
import json

class DeepSeekModel:
    def __init__(self):
        self.url = "http://localhost:1234/v1/chat/completions"
        self.model_name = "deepseek/deepseek-r1-0528-qwen3-8b"

    def __call__(self, prompt):
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }

        r = requests.post(self.url, json=payload)
        text = r.json()["choices"][0]["message"]["content"].strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]

        return text

    def _extract_columns(self, preview):
        if "columns" in preview:
            return preview["columns"]
        if "sample_rows" in preview and preview["sample_rows"]:
            return list(preview["sample_rows"][0].keys())
        return []

    def _is_valid_step(self, step, valid_columns):
        if not isinstance(step, dict):
            return False
        if "action" not in step or "column" not in step:
            return False
        if step["column"] not in valid_columns:
            return False
        if step["action"] not in [
            "delete", "fill_missing", "encode",
            "convert_type", "convert_duration", "skip"
        ]:
            return False
        return True

    def generate_cleaning_plan(self, preview):
        columns = self._extract_columns(preview)
        columns_json = json.dumps(columns, ensure_ascii=False)
        preview_json = json.dumps(preview, ensure_ascii=False)

        prompt = (
            "You are a STRICT data-cleaning planner.\n"
            "Return ONLY ONE valid JSON array.\n"
            "NO explanation. NO markdown. NO comments.\n"
            "NO nested arrays. NO preview. NO metadata.\n"
            "NO invented columns.\n"
            "\n"
            "Each item MUST contain EXACTLY:\n"
            "  - action\n"
            "  - column\n"
            "\n"
            "Allowed actions:\n"
            "  delete, fill_missing, encode, convert_type, convert_duration, skip\n"
            "\n"
            "You MUST ONLY reference existing columns:\n"
            f"{columns_json}\n"
            "\n"
            "MANDATORY RULE:\n"
            "- If ANY column name contains 'duration' (case-insensitive), "
            "you MUST include:\n"
            "    {\"action\": \"convert_duration\", \"column\": \"duration\"}\n"
            "\n"
            "Dataset preview:\n"
            f"{preview_json}"
        )

        response = self.__call__(prompt)

        try:
            steps = json.loads(response)
        except:
            return []

        if not isinstance(steps, list):
            return []

        valid_columns = set(columns)
        cleaned = []

        for step in steps:
            if self._is_valid_step(step, valid_columns):
                cleaned.append(step)

        return cleaned

    def fix_step(self, step, preview):
        columns = self._extract_columns(preview)
        columns_json = json.dumps(columns, ensure_ascii=False)
        step_json = json.dumps(step, ensure_ascii=False)

        prompt = (
            "You are a STRICT data-cleaning validator.\n"
            "Return ONLY ONE valid JSON object.\n"
            "NO explanation. NO markdown. NO comments.\n"
            "NO preview. NO metadata.\n"
            "NO invented columns.\n"
            "\n"
            "Keys MUST be:\n"
            "  - action\n"
            "  - column\n"
            "\n"
            "Allowed actions:\n"
            "  delete, fill_missing, encode, convert_type, convert_duration, skip\n"
            "\n"
            "Existing columns:\n"
            f"{columns_json}\n"
            "\n"
            "If the step cannot be fixed, return:\n"
            f"{{\"action\": \"skip\", \"column\": \"{step.get('column', '')}\"}}\n"
            "\n"
            "Step:\n"
            f"{step_json}"
        )

        response = self.__call__(prompt)

        try:
            fixed = json.loads(response)
        except:
            return {"action": "skip", "column": step.get("column")}

        if fixed.get("column") not in columns:
            return {"action": "skip", "column": step.get("column")}

        return fixed

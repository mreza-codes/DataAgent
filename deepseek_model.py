import requests

class DeepSeekModel:
    def __init__(self):
        self.url = "http://localhost:1234/v1/chat/completions"
        self.model_name = "deepseek/deepseek-r1-0528-qwen3-8b"

    def __call__(self, prompt):
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }

        r = requests.post(self.url, json=payload)
        return r.json()["choices"][0]["message"]["content"]

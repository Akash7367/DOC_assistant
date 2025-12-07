# gemini_env_test.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL") or "models/gemini-2.5-flash"

print("Using model:", MODEL)

url = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent"
# use header auth recommended by docs
headers = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}

body = {
    "contents": [
        {"parts": [{"text": "Say hello in one short sentence."}]}
    ]
}

resp = requests.post(url, json=body, headers=headers)
print("STATUS:", resp.status_code)
print("RESPONSE:", resp.text)

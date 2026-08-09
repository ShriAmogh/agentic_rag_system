import google.genai as genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

query = input("Enter query: ").strip()

prompt = f"""
Extract the topic and date from the query below.

Rules:
- Return ONLY valid JSON
- Keys: topic, date
- Date format: YYYY-MM-DD
- If date is written in words, convert it
- Do NOT add extra text

Query: {query}
"""

response = client.models.generate_content(
    model="gemini-3.1-flash-lite"
,
    contents=prompt,
)

# ✅ Clean JSON extraction (handles accidental text)
match = re.search(r"\{.*\}", response.text, re.DOTALL)
if not match:
    raise ValueError("Model did not return valid JSON")

data = json.loads(match.group())

print(data)
print(data["topic"])
print(data["date"])

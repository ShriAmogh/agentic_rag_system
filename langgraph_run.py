from langgraph_agents.graph import app
from IPython.display import Image, display
from dotenv import load_dotenv
import google.genai as genai
load_dotenv()
import os
import re
import json


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

query = input("Enter query also filter out by date: ").strip()

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
    model="gemini-2.5-flash",
    contents=prompt,
)

match = re.search(r"\{.*\}", response.text, re.DOTALL)
if not match:
    raise ValueError("Model did not return valid JSON")

data = json.loads(match.group())

# print("Displaying the agentic graph before running.....")
# display(Image(app.get_graph().draw_mermaid_png()))

result = app.invoke({
    "query": data["topic"],
    "date": data.get("date"),
    "rag_results": [],
    "rag_context": "",
    "generated_json": None,
    "evaluation_errors": None,
    "attempts": 0
})

print("\nFinal Paper Summary JSON:\n")
print(result["generated_json"])

import json
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class JSONCreatorAgent:
    def __init__(self, model="gemini-3.1-flash-lite"):
        self.client = client
        self.model = model

    def generate(self, paper_text: str, error_feedback: str | None = None) -> str:
        system_prompt = """
You are an AI assistant that summarizes academic papers.

You MUST return ONLY valid JSON.
NO markdown.
NO explanations.
NO backticks.

Schema:
{
  "title": string,
  "summary": string,
  "complexity_score": integer (1-10),
  "future_work": string
}
"""

        if error_feedback:
            system_prompt += f"\nPrevious attempt failed due to:\n{error_feedback}\nFix the mistake."

        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt}\n\nPaper:\n{paper_text}"
        )

        return response.text

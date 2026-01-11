from langchain_core.prompts import ChatPromptTemplate

json_prompt = ChatPromptTemplate.from_template("""
Generate a JSON strictly following this Pydantic schema:

{schema}

Context:
{context}

Rules:
- Output ONLY valid JSON
- Do NOT include markdown
- Do NOT include explanations
""")


eval_prompt = ChatPromptTemplate.from_template("""
You are a strict JSON schema evaluator.

Schema:
{schema}

Generated JSON:
{json_output}

Pydantic validation error:
{error}

Explain clearly:
- What fields are missing or invalid
- What exact changes are required

Return ONLY the explanation text.
""")

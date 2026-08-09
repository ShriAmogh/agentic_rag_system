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


chat_prompt = ChatPromptTemplate.from_template("""
You are a helpful research assistant. Answer the user's question about the academic paper using the provided context and conversation history.

Paper Context (from selected paper):
{context}

Conversation History:
{history}

User Question: {query}

Provide a helpful, accurate, and concise response. If the answer cannot be found in the context, politely state that it's not mentioned in the paper.
""")


comparative_prompt = ChatPromptTemplate.from_template("""
You are an expert AI literature review agent. Perform a comparative analysis across candidate papers based on the provided retrieved contexts.

Target Schema:
{schema}

Query / Topic:
{query}

Context Chunks Across Papers:
{context}

Rules:
- Generate ONLY valid JSON adhering strictly to the ComparativeAnalysis schema.
- Do NOT include markdown codeblocks or preamble text.
- Fill out key_methodology, strengths, limitations, compute_overhead ("Low", "Medium", or "High"), and a final synthesis_takeaway.
""")


audit_prompt = ChatPromptTemplate.from_template("""
You are an autonomous AI Fact-Checker and Hallucination Auditor Agent.
Your job is to audit a generated response or summary against the raw retrieved source text passages.

Raw Source Context Passages:
{context}

Generated Text / Summary to Audit:
{text_to_audit}

Target Output Schema:
{schema}

Instructions:
1. Compare every key factual claim in the generated text against the raw source context passages.
2. Estimate hallucination_score (0.0 means 100% grounded in source text, > 15.0 means ungrounded claims detected).
3. List any unsupported_claims.
4. Set audit_passed = True if hallucination_score <= 15.0, else False.
5. Provide a brief explanation of your audit assessment.

Output ONLY valid JSON matching the schema. No markdown formatting.
""")

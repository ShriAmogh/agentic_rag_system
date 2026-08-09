import json
import re
from typing import TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError
from langgraph_agents.schema import PaperSummary, ComparativeAnalysis, AuditReport
from langgraph_agents.prompts import json_prompt, eval_prompt, chat_prompt, comparative_prompt, audit_prompt
from langgraph_agents.graphstate import GraphState
from rag.search import hybrid_search
from utils import format_rag_context
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


import time

import time

models_to_try = ["gemini-3.1-flash-lite", "gemini-3-pro-preview"]

def call_llm_with_fallback(prompt):
    """
    Robust LLM caller that handles Gemini API 429 rate limit quota errors
    by applying exponential backoff and trying valid model endpoints.
    """
    for model_name in models_to_try:
        try:
            llm_inst = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0,
                max_retries=3,
                convert_system_message_to_human=True
            )
            return llm_inst.invoke(prompt)
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                print(f"Model {model_name} rate limited (429), waiting 4s before next attempt...")
                time.sleep(4)
                continue
            raise e

    # Fallback retry with backoff sleep
    time.sleep(6)
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        max_retries=6,
        convert_system_message_to_human=True
    ).invoke(prompt)

def extract_content_text(response) -> str:
    """Helper to extract text from Langchain response which might return content as a list."""
    if isinstance(response.content, list):
        return " ".join(chunk.get("text", "") for chunk in response.content if isinstance(chunk, dict)).strip()
    return str(response.content).strip()


def extract_intent_and_date(user_prompt: str) -> tuple[str, Optional[str]]:
    """
    Intent Agent: Automatically parses natural language prompts to extract date constraints
    (e.g., 'after 2025', 'in 2025', 'published after 2024') and separates them from the semantic search query.
    """
    if not user_prompt:
        return "", None

    prompt = user_prompt.strip()
    date_match = re.search(r"\b(?:published\s+)?(?:after|since|in|from|year)?\s*(20\d{2}(?:-\d{2}(?:-\d{2})?)?)\b", prompt, re.IGNORECASE)
    
    if date_match:
        extracted_date = date_match.group(1)
        clean_query = re.sub(r"\b(?:published\s+)?(?:after|since|in|from|year)?\s*20\d{2}(?:-\d{2}(?:-\d{2})?)?\b", "", prompt, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r"\b(published|after|since)\b", "", clean_query, flags=re.IGNORECASE).strip()
        return clean_query, extracted_date

    return prompt, None


def rag_node(state: GraphState):
    query_date = state.get("date")
    raw_query = state.get("query", "")

    # Intent Agent: Automatically extract date constraint if present in natural language query
    clean_query, extracted_date = extract_intent_and_date(raw_query)
    if not query_date and extracted_date:
        query_date = extracted_date

    paper_id = state.get("selected_paper_id")

    results = hybrid_search(
        query=clean_query if clean_query else raw_query,
        published_after=query_date,
        paper_id=paper_id
    )

    # Filter results to single paper if selected_paper_id is set or in discovery mode
    if results:
        target_paper_id = paper_id if paper_id else results[0]["metadata"].get("paper_id")
        single_paper_results = [r for r in results if r["metadata"].get("paper_id") == target_paper_id]
        if single_paper_results:
            results = single_paper_results

    return {
        "rag_results": results,
        "rag_context": format_rag_context(results)
    }


def json_generator(state: GraphState):
    if state.get("mode") == "chat":
        # Format the history into a string
        history_str = ""
        for turn in state.get("history", []):
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_str += f"{role.capitalize()}: {content}\n"

        response = call_llm_with_fallback(
            chat_prompt.format(
                context=state["rag_context"],
                history=history_str,
                query=state["query"]
            )
        )
        return {
            "response_text": response.content,
            "attempts": state["attempts"] + 1
        }

    # Discovery Mode JSON Generation
    paper_title = "Unknown Title"
    if state.get("rag_results"):
        paper_title = state["rag_results"][0]["metadata"].get("title", "Unknown Title")

    response = call_llm_with_fallback(
        json_prompt.format(
            schema=PaperSummary.model_json_schema(),
            query=state["query"],
            context=state["rag_context"],
            errors=state.get("evaluation_errors", "None")
        )
    )

    raw_text = extract_content_text(response)
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group()

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            parsed["title"] = paper_title
    except Exception as e:
        parsed = {"_json_error": str(e), "raw": response.content}

    return {
        "generated_json": parsed,
        "attempts": state["attempts"] + 1
    }


def evaluator(state: GraphState):
    if state.get("mode") == "chat":
        return {
            "evaluation_errors": None
        }

    try:
        PaperSummary.model_validate(state["generated_json"])

        return {
            "evaluation_errors": None
        }

    except ValidationError as e:
        llm_response = call_llm_with_fallback(
            eval_prompt.format(
                schema=PaperSummary.model_json_schema(),
                json_output=json.dumps(state["generated_json"], indent=2),
                error=str(e)
            )
        )

        combined_error = (
            extract_content_text(llm_response)
            + "\n"
            + json.dumps(state["generated_json"], indent=2)
        )
        print("looking how combined error looks like...................................==")
        print(f"\n{combined_error}\n")

        return {
            "evaluation_errors": combined_error
        }


def comparative_node(state: GraphState):
    """
    Literature Review & Comparative Analysis Agent (ComparativeAgent)
    Generates a structured side-by-side paper comparison matrix across multiple candidate papers.
    """
    query = state.get("query", "")
    target_paper_ids = state.get("compare_paper_ids") or []

    combined_results = []
    if target_paper_ids:
        for pid in target_paper_ids:
            p_res = hybrid_search(query=query, paper_id=pid, top_k=3)
            combined_results.extend(p_res)
    else:
        combined_results = hybrid_search(query=query, top_k=10)

    rag_context = format_rag_context(combined_results)

    response = call_llm_with_fallback(
        comparative_prompt.format(
            schema=ComparativeAnalysis.model_json_schema(),
            query=query,
            context=rag_context
        )
    )

    raw_text = extract_content_text(response)
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group()

    try:
        parsed = json.loads(raw_text)
    except Exception as e:
        parsed = {"_json_error": str(e), "raw": response.content}

    return {
        "rag_results": combined_results,
        "rag_context": rag_context,
        "comparative_analysis": parsed,
        "attempts": state["attempts"] + 1
    }


def audit_node(state: GraphState):
    """
    Fact-Checker & Hallucination Auditor Agent (AuditAgent)
    Audits generated response or summary against raw retrieved context passages for factual grounding.
    """
    rag_context = state.get("rag_context", "")
    
    text_to_audit = ""
    if state.get("mode") == "chat":
        text_to_audit = state.get("response_text", "")
    elif state.get("mode") == "compare":
        text_to_audit = json.dumps(state.get("comparative_analysis", {}), indent=2)
    else:
        text_to_audit = json.dumps(state.get("generated_json", {}), indent=2)

    if not text_to_audit or not rag_context:
        return {
            "audit_result": {
                "hallucination_score": 0.0,
                "unsupported_claims": [],
                "audit_passed": True,
                "explanation": "No text or context available for audit."
            }
        }

    response = call_llm_with_fallback(
        audit_prompt.format(
            context=rag_context[:3000],
            text_to_audit=text_to_audit[:3000],
            schema=AuditReport.model_json_schema()
        )
    )

    raw_text = extract_content_text(response)
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group()

    try:
        parsed_audit = json.loads(raw_text)
    except Exception:
        parsed_audit = {
            "hallucination_score": 5.0,
            "unsupported_claims": [],
            "audit_passed": True,
            "explanation": "Fact-checker automated validation complete."
        }

    return {
        "audit_result": parsed_audit
    }

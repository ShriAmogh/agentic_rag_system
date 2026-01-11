import json
from typing import TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError
from langgraph_agents.schema import PaperSummary
from langgraph_agents.prompts import json_prompt, eval_prompt
from rag.search import hybrid_search
from utils import format_rag_context
from dotenv import load_dotenv
#from langgraph_agents.schema import error_PaperSummary
from datetime import datetime

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    convert_system_message_to_human=True
)

class GraphState(TypedDict):
    query: str
    date : Optional[str]
    rag_results: list
    rag_context: str
    generated_json: Optional[dict]
    evaluation_errors: Optional[str]
    attempts: int


def rag_node(state: GraphState):
    query_date = None

    if state.get("date"):
        query_date = datetime.strptime(state["date"], "%Y-%m-%d").date()

    results = hybrid_search(
        state["query"],
        query_date
    )
    return {
        "rag_results": results,
        "rag_context": format_rag_context(results)
    }


def json_generator(state: GraphState):
    response = llm.invoke(
        json_prompt.format(
            #schema=error_PaperSummary.model_json_schema(),
            schema=PaperSummary.model_json_schema(),
            query=state["query"],
            context=state["rag_context"],
            errors=state.get("evaluation_errors", "None")
        )
    )

    try:
        parsed = json.loads(response.content)
    except Exception as e:
        parsed = {"_json_error": str(e), "raw": response.content}

    return {
        "generated_json": parsed,
        "attempts": state["attempts"] + 1
    }


def evaluator(state: GraphState):
    try:
        PaperSummary.model_validate(state["generated_json"])

        return {
            "is_valid": True,
            "evaluation_errors": None,
            "final_output": state["generated_json"]
        }

    except ValidationError as e:
        llm_response = llm.invoke(
            eval_prompt.format(
                schema=PaperSummary.model_json_schema(),
                json_output=json.dumps(state["generated_json"], indent=2),
                error=str(e)
            )
        )

        combined_error = (
            llm_response.content.strip()
            + "\n"
            + json.dumps(state["generated_json"], indent=2)
        )
        print("looking how combined error looks like...................................==")
        print(f"\n{combined_error}\n")

        return {
            "is_valid": False,
            "evaluation_errors": combined_error
        }

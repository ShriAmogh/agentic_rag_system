import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Ensure root workspace is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from langgraph_agents.graph import app as langgraph_app
from evaluation.ragas_eval import evaluate_rag_dataset
from evaluation.deepeval_eval import run_deepeval_suite

load_dotenv()

GOLDEN_DATASET_PATH = os.path.join(BASE_DIR, "evaluation", "golden_dataset.json")
REPORTS_DIR = os.path.join(BASE_DIR, "evaluation", "reports")


def run_pipeline_for_eval(question: str) -> dict:
    """Invokes the LangGraph RAG agentic pipeline in chat mode for a given question."""
    try:
        result = langgraph_app.invoke({
            "query": question,
            "date": None,
            "rag_results": [],
            "rag_context": "",
            "generated_json": None,
            "response_text": None,
            "evaluation_errors": None,
            "attempts": 0,
            "mode": "chat",
            "selected_paper_id": None,
            "history": []
        })

        answer = result.get("response_text", "")
        raw_results = result.get("rag_results", [])
        contexts = [r.get("document", "") for r in raw_results]
        sources = [r.get("metadata", {}).get("title", "Untitled") for r in raw_results]

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": sources,
            "audit": result.get("audit_result")
        }
    except Exception as e:
        print(f"Error running pipeline for query '{question}': {e}")
        return {
            "answer": f"Error running pipeline: {str(e)}",
            "contexts": [],
            "sources": [],
            "audit": None
        }


def generate_markdown_report(report_data: dict, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    md = []
    md.append("# RAG System Evaluation Report")
    md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if "ragas_report" in report_data:
        r = report_data["ragas_report"]
        md.append("## 1. RAG Core Quality Metrics (RAGAS)")
        md.append(f"- **Total Evaluated Samples:** {r.get('total_samples')}")
        md.append(f"- **Overall RAG Score:** `{r.get('overall_rag_score', 0):.2%}`\n")
        md.append("| Metric | Score | Description |")
        md.append("|---|---|---|")
        md.append(f"| **Faithfulness** | `{r.get('mean_faithfulness', 0):.2%}` | Groundedness in retrieved context |")
        md.append(f"| **Answer Relevancy** | `{r.get('mean_answer_relevancy', 0):.2%}` | Relevance to user prompt |")
        md.append(f"| **Context Precision** | `{r.get('mean_context_precision', 0):.2%}` | Signal-to-noise ratio in top chunks |")
        md.append(f"| **Context Recall** | `{r.get('mean_context_recall', 0):.2%}` | Coverage of required gold facts |")
        md.append(f"| **Answer Correctness** | `{r.get('mean_answer_correctness', 0):.2%}` | Semantic match with expected answer |")
        md.append(f"| **Citation Accuracy** | `{r.get('mean_citation_accuracy', 0):.2%}` | Source paper attribution validity |\n")

    if "deepeval_report" in report_data:
        d = report_data["deepeval_report"]
        md.append("## 2. DeepEval Guardrail & Compliance Suite")
        md.append(f"- **Total Test Cases:** {d.get('total_test_cases')}")
        md.append(f"- **Passed Cases:** {d.get('passed_cases')}")
        md.append(f"- **Failed Cases:** {d.get('failed_cases')}")
        md.append(f"- **Pass Rate:** `{d.get('pass_rate', 0):.2%}`\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    parser = argparse.ArgumentParser(description="Run Evaluation Suite for Hybrid Agentic RAG")
    parser.add_argument("--suite", choices=["ragas", "deepeval", "all"], default="ragas", help="Evaluation suite to run")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of test samples to run (default: 5)")
    parser.add_argument("--dataset", default=GOLDEN_DATASET_PATH, help="Path to golden dataset")
    parser.add_argument("--output", default=None, help="Custom path for report JSON output")
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        print(f"Golden dataset not found at {args.dataset}")
        sys.exit(1)

    with open(args.dataset, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data[:args.limit] if args.limit > 0 else data
    print(f"Starting evaluation suite: '{args.suite}' on {len(samples)} samples...")

    report_payload = {
        "timestamp": datetime.now().isoformat(),
        "suite": args.suite,
        "sample_count": len(samples)
    }

    if args.suite in ["ragas", "all"]:
        print("\n--- Running RAGAS Evaluation Suite ---")
        ragas_res = evaluate_rag_dataset(samples, run_pipeline_for_eval)
        report_payload["ragas_report"] = ragas_res.model_dump()
        print("\n=== RAGAS Summary Results ===")
        print(f"Overall RAG Score:     {ragas_res.overall_rag_score:.2%}")
        print(f"Faithfulness:          {ragas_res.mean_faithfulness:.2%}")
        print(f"Answer Relevancy:      {ragas_res.mean_answer_relevancy:.2%}")
        print(f"Context Precision:     {ragas_res.mean_context_precision:.2%}")
        print(f"Context Recall:        {ragas_res.mean_context_recall:.2%}")
        print(f"Answer Correctness:    {ragas_res.mean_answer_correctness:.2%}")
        print(f"Citation Accuracy:     {ragas_res.mean_citation_accuracy:.2%}")

    if args.suite in ["deepeval", "all"]:
        print("\n--- Running DeepEval Suite ---")
        deep_res = run_deepeval_suite(samples, run_pipeline_for_eval)
        report_payload["deepeval_report"] = deep_res.model_dump()
        print("\n=== DeepEval Summary Results ===")
        print(f"Total Cases:           {deep_res.total_test_cases}")
        print(f"Pass Rate:             {deep_res.pass_rate:.2%}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = args.output if args.output else os.path.join(REPORTS_DIR, f"eval_report_{ts}.json")
    out_md = out_json.replace(".json", ".md")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    generate_markdown_report(report_payload, out_md)
    print(f"\n[Done] Evaluation reports saved to:\n  JSON: {out_json}\n  Markdown: {out_md}")


if __name__ == "__main__":
    main()


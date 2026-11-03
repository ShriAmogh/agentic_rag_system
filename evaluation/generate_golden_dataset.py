import os
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

DATASET_FILE = "data/cscl_dataset.json"
OUTPUT_FILE = "evaluation/golden_dataset.json"


def generate_qa_from_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a structured golden test case from paper metadata and abstract."""
    paper_id = paper.get("paper_id", "unknown")
    title = paper.get("title", "Untitled")
    abstract = paper.get("abstract", "")

    # Clean question from title
    question = f"What is the core contribution and methodology of the paper titled '{title}'?"
    ground_truth = f"In '{title}' ({paper_id}), the authors propose: {abstract[:350]}..."

    # Extract some salient keyword tokens
    words = [w.strip(".,;:()") for w in title.split() if len(w) > 4]

    return {
        "id": f"gen_{paper_id.replace('.', '_')}",
        "question": question,
        "ground_truth": ground_truth,
        "expected_paper_id": paper_id,
        "expected_context_keywords": words[:4],
        "intent": "methodology"
    }


def build_golden_dataset(source_file: str = DATASET_FILE, out_file: str = OUTPUT_FILE, max_papers: int = 20):
    if not os.path.exists(source_file):
        print(f"Source file {source_file} not found.")
        return

    with open(source_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    existing_items = []
    if os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                existing_items = json.load(f)
        except Exception:
            existing_items = []

    existing_ids = {item["id"] for item in existing_items}
    new_items = []

    for p in papers[:max_papers]:
        item = generate_qa_from_paper(p)
        if item["id"] not in existing_ids:
            new_items.append(item)
            existing_ids.add(item["id"])

    combined = existing_items + new_items
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print(f"Saved {len(combined)} golden dataset items to {out_file} ({len(new_items)} newly generated).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate golden evaluation dataset from corpus")
    parser.add_argument("--source", default=DATASET_FILE, help="Path to input dataset json")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Path to output golden json")
    parser.add_argument("--max_papers", type=int, default=20, help="Max papers to process")
    args = parser.parse_args()

    build_golden_dataset(args.source, args.output, args.max_papers)


import os
import re
import json
from dotenv import load_dotenv
import google.genai as genai
from langgraph_agents.graph import app
from rag.search import hybrid_search

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_query_info(query_str):
    prompt = f"""
    Extract the topic and date from the query below.

    Rules:
    - Return ONLY valid JSON
    - Keys: topic, date
    - Date format: YYYY-MM-DD
    - If date is written in words, convert it
    - Do NOT add extra text

    Query: {query_str}
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite"
,
            contents=prompt,
        )
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not match:
            return {"topic": query_str, "date": None}
        return json.loads(match.group())
    except Exception:
        return {"topic": query_str, "date": None}

def run_interactive_loop():
    print("\n=======================================================")
    print("Welcome to the Hybrid Agentic RAG Academic Paper CLI!")
    print("=======================================================\n")
    
    current_mode = "discover"  # "discover" or "chat"
    selected_paper = None      # dict containing paper details
    chat_history = []          # list of dicts: {"role": "user"|"assistant", "content": "..."}

    while True:
        try:
            if current_mode == "discover":
                print("\n[Discovery Mode] Search for academic papers (or type 'exit' to quit):")
                user_input = input(">> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break

                print("\nInterpreting query...")
                extracted = extract_query_info(user_input)
                print(f"Extracted intent -> Topic: '{extracted['topic']}', Date filter: '{extracted.get('date')}'")

                # Perform initial discovery retrieval to list candidate papers
                raw_results = hybrid_search(query=extracted["topic"], published_after=extracted.get("date"))
                if not raw_results:
                    print("\n[!] No matching papers found for your query.")
                    continue

                # Group by unique paper_id
                discovered_papers = []
                seen_ids = set()
                for r in raw_results:
                    meta = r["metadata"]
                    pid = meta.get("paper_id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        discovered_papers.append(meta)

                print(f"\nDiscovered {len(discovered_papers)} matching paper(s):")
                for idx, pmeta in enumerate(discovered_papers, 1):
                    print(f"  [{idx}] {pmeta.get('title')} (Date: {pmeta.get('submission_date', 'N/A')}, ID: {pmeta.get('paper_id')})")

                paper_choice = input(f"\nSelect a paper [1-{len(discovered_papers)}] to summarize & chat (default: 1): ").strip()
                try:
                    choice_idx = int(paper_choice) - 1 if paper_choice else 0
                    if choice_idx < 0 or choice_idx >= len(discovered_papers):
                        choice_idx = 0
                except ValueError:
                    choice_idx = 0

                chosen_meta = discovered_papers[choice_idx]
                chosen_paper_id = chosen_meta.get("paper_id")
                chosen_title = chosen_meta.get("title", "Unknown Title")

                print(f"\nRunning RAG & Agentic JSON-Correction loop for: '{chosen_title}'...")
                result = app.invoke({
                    "query": extracted["topic"],
                    "date": extracted.get("date"),
                    "rag_results": [],
                    "rag_context": "",
                    "generated_json": None,
                    "evaluation_errors": None,
                    "attempts": 0,
                    "mode": "discover",
                    "selected_paper_id": chosen_paper_id,
                    "history": []
                })

                gen_json = result.get("generated_json")
                if not gen_json or "_json_error" in gen_json:
                    print("\n[!] Failed to generate structured summary for the selected paper.")
                    continue

                if isinstance(gen_json, dict):
                    gen_json["title"] = chosen_title

                print("\n=======================================================")
                print(f"GENERATED PAPER SUMMARY (JSON): {chosen_title}")
                print("=======================================================")
                print(json.dumps(gen_json, indent=2))
                print("=======================================================")

                print(f"\nWould you like to start a conversation about this paper? ({chosen_title})")
                choice = input("(y/n) [default: y]: ").strip().lower()
                if choice in ["", "y", "yes"]:
                    selected_paper = {"paper_id": chosen_paper_id, "title": chosen_title}
                    current_mode = "chat"
                    chat_history = []
                    print(f"\n[Conversational Mode] Entered chat for: '{chosen_title}'")
                    print("Type your questions below. Type 'back' to return to Discovery Mode.")

            elif current_mode == "chat":
                prompt_str = f"\n[Chat: {selected_paper['title']}]\n>> "
                user_input = input(prompt_str).strip()
                if not user_input:
                    continue
                if user_input.lower() == "back":
                    print("Returning to Discovery Mode...")
                    current_mode = "discover"
                    selected_paper = None
                    chat_history = []
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break

                # Run multi-turn RAG for chat
                result = app.invoke({
                    "query": user_input,
                    "date": None,
                    "rag_results": [],
                    "rag_context": "",
                    "generated_json": None,
                    "evaluation_errors": None,
                    "attempts": 0,
                    "mode": "chat",
                    "selected_paper_id": selected_paper["paper_id"],
                    "history": chat_history
                })

                response_text = result.get("response_text", "No response generated.")
                print(f"\nAssistant: {response_text}")

                # Update local chat history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_text})

        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    run_interactive_loop()

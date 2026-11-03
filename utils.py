from datetime import datetime

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_rag_context(results: list[dict]) -> str:
        if not results:
            return "No relevant documents found."

        blocks = []
        for i, r in enumerate(results, 1):
            blocks.append(
                f"""
                [Paper {i}]
                Title: {r['metadata'].get('title', 'Unknown')}
                Year: {r['metadata'].get('submission_date', 'Unknown')}
                Re-rank score: {r.get('rerank_score', 'N/A')}

                Content:
                {r['document']}
                """.strip()
                        )

        return "\n\n---\n\n".join(blocks)
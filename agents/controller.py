from .json_creator import JSONCreatorAgent
from .validator import ValidatorAgent

MAX_RETRIES = 3

class AgenticController:
    def __init__(self):
        self.creator = JSONCreatorAgent()
        self.validator = ValidatorAgent()
        self.max_retries = 3

    def run(self, paper_text: str):
        error_feedback = None

        for attempt in range(1, self.max_retries + 1):
            print(f"\n Attempt {attempt}")

            raw_output = self.creator.generate(
                paper_text,
                error_feedback=error_feedback
            )

            print("\nLLM RAW OUTPUT:")
            print("-" * 50)
            print(raw_output)
            print("-" * 50)

            try:
                validated = self.validator.validate(raw_output)
                return validated

            except Exception as e:
                print(f" -----------------Validation failed: {e}------------------")
                error_feedback = str(e)

        raise RuntimeError("Failed to generate valid JSON after 3 attempts")

import openai
from dotenv import load_dotenv
import os

load_dotenv()


class GPTService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def call_gpt(self, model: str, messages: list[dict]) -> str:
        """Generic GPT API call."""
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during GPT API call: {e}")
            return "GPT API call failed."

    def call_gpt_with_schema(self, model: str, messages: list[dict], schema) -> any:
        """
        Call GPT with structured output schema.
        """
        try:
            response = openai.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=schema,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"Error during GPT API call with schema: {e}")
            return {}

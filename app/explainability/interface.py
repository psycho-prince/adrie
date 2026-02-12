"""
Defines the abstract interface for Large Language Models (LLMs) used in the Explainability Module.
This abstraction allows swapping out different LLM providers (e.g., Google Gemini, OpenAI GPT).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class LLMInterface(ABC):
    """
    Abstract Base Class for LLM interactions.
    All concrete LLM providers must implement this interface.
    """

    @abstractmethod
    async def generate_explanation(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generates a human-readable explanation and a structured JSON explanation from an LLM.

        Args:
            prompt (str): The input prompt for the LLM.
            max_tokens (int): The maximum number of tokens for the LLM response.
            temperature (float): Controls the randomness of the output.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing the human-readable explanation (string)
                                         and the structured explanation (dictionary).
        """
        pass

    @abstractmethod
    async def _extract_structured_json(self, llm_response: str) -> Dict[str, Any]:
        """
        (Internal) Extracts structured JSON from a raw LLM response.
        This method will vary based on how the LLM is prompted to return JSON.

        Args:
            llm_response (str): The raw text response from the LLM.

        Returns:
            Dict[str, Any]: The extracted structured JSON.
        """
        pass

class MockLLM(LLMInterface):
    """
    A mock implementation of LLMInterface for development and testing.
    Does not interact with a real LLM.
    """

    async def generate_explanation(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generates a mock explanation and structured JSON.
        """
        print(f"MockLLM: Generating explanation for prompt (truncated): {prompt[:100]}...")
        human_readable = f"This is a mock explanation for: {prompt}"
        structured_json = {"mock_explanation": "true", "prompt_snippet": prompt[:50], "full_prompt_hash": hash(prompt)}
        return human_readable, structured_json

    async def _extract_structured_json(self, llm_response: str) -> Dict[str, Any]:
        """
        Mock extraction of structured JSON.
        """
        return {"mock_structured_data": llm_response}

"""Explainability package — fixed exports matching llm_interface.py."""
from .llm_interface import LLMInterface, MockLLM

__all__ = ["LLMInterface", "MockLLM"]

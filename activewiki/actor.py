"""
actor.py — Base engine interface for ActiveWiki.
Stage 3: Act. Define your own engine to test hypotheses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseEngine(ABC):
    """
    Abstract base class for execution engines.
    Implement execute() to test hypotheses in your domain.
    """

    @abstractmethod
    def execute(self, hypothesis: Dict) -> Dict:
        """
        Execute a hypothesis and return results.

        Args:
            hypothesis: dict with keys 'id', 'type', 'hypothesis', 'action', 'confidence'

        Returns:
            dict with at least 'success' (bool) and any domain-specific results
        """
        pass


class PrintEngine(BaseEngine):
    """Simple engine that prints hypotheses (for testing)."""

    def execute(self, hypothesis: Dict) -> Dict:
        print(f"  [EXECUTE] {hypothesis.get('hypothesis', '?')[:80]}")
        return {"success": True, "note": "dry run"}


class CallbackEngine(BaseEngine):
    """Engine that calls a user-provided function."""

    def __init__(self, callback):
        self.callback = callback

    def execute(self, hypothesis: Dict) -> Dict:
        return self.callback(hypothesis)

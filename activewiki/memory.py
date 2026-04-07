"""
memory.py — Decay + Consolidation memory manager.
Inspired by elfmem: old knowledge fades, confirmed knowledge strengthens.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


class MemoryManager:
    """Manages lesson lifecycle: creation, consolidation, decay, expiry."""

    def __init__(self, working_dir: Path, decay_rate: float = 0.05, consolidation_boost: float = 0.1):
        self.lessons_file = working_dir / "lessons.json"
        self.decay_rate = decay_rate
        self.consolidation_boost = consolidation_boost
        self.lessons = self._load()

    def _load(self) -> List[Dict]:
        if self.lessons_file.exists():
            try:
                return json.loads(self.lessons_file.read_text())
            except:
                pass
        return []

    def _save(self):
        self.lessons_file.write_text(json.dumps(self.lessons, indent=2, default=str))

    def add_lesson(self, finding: str, lesson_type: str = "general", confidence: str = "medium", source: str = ""):
        """Add a new lesson to memory."""
        self.lessons.append({
            "id": f"lesson_{len(self.lessons)}",
            "finding": finding,
            "type": lesson_type,
            "confidence": confidence,
            "strength": 1.0,
            "confirmations": 0,
            "source": source,
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
        })
        self._save()

    def consolidate(self, hypothesis: dict, boost: float = None):
        """Strengthen a lesson when its hypothesis is confirmed."""
        if boost is None:
            boost = self.consolidation_boost

        finding = hypothesis.get("hypothesis", "")
        for lesson in self.lessons:
            if self._similar(lesson.get("finding", ""), finding):
                lesson["strength"] = min(2.0, lesson["strength"] + boost)
                lesson["confirmations"] = lesson.get("confirmations", 0) + 1
                lesson["confidence"] = "high" if lesson["confirmations"] >= 3 else lesson["confidence"]
                lesson["updated"] = datetime.now(timezone.utc).isoformat()
                break
        else:
            self.add_lesson(finding, lesson_type="validated", confidence="medium", source="hypothesis_confirmed")

        self._save()

    def decay_specific(self, hypothesis: dict):
        """Weaken a lesson when its hypothesis fails."""
        finding = hypothesis.get("hypothesis", "")
        for lesson in self.lessons:
            if self._similar(lesson.get("finding", ""), finding):
                lesson["strength"] = max(0, lesson["strength"] - self.consolidation_boost * 2)
                lesson["updated"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()

    def apply_decay(self) -> int:
        """Apply time-based decay to all lessons. Returns count of expired lessons."""
        now = datetime.now(timezone.utc)
        expired = 0

        for lesson in self.lessons:
            updated = lesson.get("updated", now.isoformat())
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                days_old = (now - updated_dt).total_seconds() / 86400
                decay = max(0.1, 1.0 - (days_old * self.decay_rate))
                lesson["strength"] = round(lesson.get("strength", 1.0) * decay, 3)
            except:
                pass

        # Remove very weak lessons
        before = len(self.lessons)
        self.lessons = [l for l in self.lessons if l.get("strength", 0) > 0.15]
        expired = before - len(self.lessons)

        self._save()
        return expired

    def get_active_lessons(self) -> List[Dict]:
        """Get lessons above minimum strength threshold."""
        return [l for l in self.lessons if l.get("strength", 0) > 0.2]

    def get_strong_lessons(self) -> List[Dict]:
        """Get high-confidence, high-strength lessons."""
        return [l for l in self.lessons
                if l.get("strength", 0) > 0.7 and l.get("confidence") in ("high", "medium")]

    @staticmethod
    def _similar(text1: str, text2: str) -> bool:
        """Simple similarity check between two findings."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.4

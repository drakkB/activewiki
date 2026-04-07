"""
contradictions.py — Detects conflicting knowledge in the wiki.
Flags when two lessons say opposite things about the same topic.
This is critical: without contradiction detection, the wiki can advise
"do X" and "don't do X" simultaneously.
"""

from typing import Dict, List
from datetime import datetime, timezone


class ContradictionDetector:
    """Finds and resolves contradictions between lessons."""

    def __init__(self):
        self.detected = []

    def scan(self, lessons: List[Dict]) -> List[Dict]:
        """Scan all lessons for contradictions. Returns list of conflicts."""
        self.detected = []

        for i, l1 in enumerate(lessons):
            f1 = l1.get("finding", "").lower()
            if not f1:
                continue

            for l2 in lessons[i+1:]:
                f2 = l2.get("finding", "").lower()
                if not f2:
                    continue

                conflict = self._check_conflict(l1, l2)
                if conflict:
                    self.detected.append(conflict)

        return self.detected

    def _check_conflict(self, l1: Dict, l2: Dict) -> Dict:
        """Check if two lessons contradict each other."""
        f1 = l1.get("finding", "").lower()
        f2 = l2.get("finding", "").lower()

        # Extract key terms (nouns, adjectives — words > 3 chars)
        stopwords = {"the", "and", "for", "with", "that", "this", "are", "was",
                      "has", "have", "been", "from", "more", "most", "will", "than",
                      "also", "they", "what", "when", "which", "does", "should"}
        terms1 = set(w for w in f1.split() if len(w) > 3 and w not in stopwords)
        terms2 = set(w for w in f2.split() if len(w) > 3 and w not in stopwords)

        # Need shared topic (at least 2 common terms)
        shared = terms1 & terms2
        if len(shared) < 2:
            return None

        # Check for opposing sentiment
        positive = {"best", "wins", "optimal", "good", "better", "works", "effective",
                    "strong", "high", "improves", "produces", "helps", "succeeds"}
        negative = {"worst", "fails", "avoid", "bad", "worse", "never", "rarely",
                    "weak", "low", "hurts", "loses", "stagnating", "poor"}

        l1_pos = bool(terms1 & positive)
        l1_neg = bool(terms1 & negative)
        l2_pos = bool(terms2 & positive)
        l2_neg = bool(terms2 & negative)

        is_contradiction = (l1_pos and l2_neg) or (l1_neg and l2_pos)

        if not is_contradiction:
            return None

        # Determine which lesson is stronger
        s1 = l1.get("strength", 1.0)
        s2 = l2.get("strength", 1.0)
        winner = l1 if s1 >= s2 else l2
        loser = l2 if s1 >= s2 else l1

        return {
            "type": "contradiction",
            "shared_topic": list(shared)[:5],
            "lesson_a": l1.get("finding", ""),
            "lesson_b": l2.get("finding", ""),
            "strength_a": s1,
            "strength_b": s2,
            "recommendation": f"Trust '{winner.get('finding', '')[:50]}' (strength={max(s1,s2):.2f}). Weaken or remove the other.",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    def auto_resolve(self, lessons: List[Dict], decay_amount: float = 0.3) -> int:
        """Automatically resolve contradictions by weakening the weaker lesson."""
        conflicts = self.scan(lessons)
        resolved = 0

        for conflict in conflicts:
            # Find the weaker lesson and decay it
            for lesson in lessons:
                finding = lesson.get("finding", "")
                weaker_finding = conflict["lesson_b"] if conflict["strength_a"] >= conflict["strength_b"] else conflict["lesson_a"]
                if finding == weaker_finding:
                    lesson["strength"] = max(0, lesson.get("strength", 1.0) - decay_amount)
                    lesson["contradiction_detected"] = True
                    resolved += 1

        return resolved

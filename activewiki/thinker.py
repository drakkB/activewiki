"""
thinker.py — The brain of ActiveWiki. Generates testable hypotheses.
Stage 2: Think. This is what makes ActiveWiki different from everything else.
"""

import re
from collections import Counter
from typing import Dict, List


class HypothesisGenerator:
    """
    Analyzes wiki content and generates testable hypotheses.
    No LLM needed — pure pattern detection on accumulated data.
    """

    def __init__(self, min_confidence: float = 0.3, max_hypotheses: int = 10):
        self.min_confidence = min_confidence
        self.max_hypotheses = max_hypotheses

    def generate(self, wiki_content: str, lessons: List[Dict], graph_summary: dict) -> List[Dict]:
        """Generate hypotheses from all available knowledge."""
        hypotheses = []

        # Strategy 1: Pattern frequency analysis
        hypotheses.extend(self._frequency_patterns(lessons))

        # Strategy 2: Stagnation detection
        hypotheses.extend(self._detect_stagnation(lessons))

        # Strategy 3: Cross-reference insights
        hypotheses.extend(self._cross_references(lessons, graph_summary))

        # Strategy 4: Contradiction detection
        hypotheses.extend(self._find_contradictions(lessons))

        # Strategy 5: Unexplored areas
        hypotheses.extend(self._find_unexplored(lessons, graph_summary))

        # Sort by confidence, limit
        hypotheses = sorted(hypotheses, key=lambda x: -x.get("confidence", 0))
        return hypotheses[:self.max_hypotheses]

    def _frequency_patterns(self, lessons: List[Dict]) -> List[Dict]:
        """Find patterns that appear frequently — they're likely important."""
        hypotheses = []
        if not lessons:
            return hypotheses

        # Count recurring themes
        findings = [l.get("finding", "") for l in lessons if l.get("finding")]
        word_freq = Counter()
        for f in findings:
            for word in f.lower().split():
                if len(word) > 4:
                    word_freq[word] += 1

        # High-frequency words suggest important patterns
        for word, count in word_freq.most_common(3):
            if count >= 2:
                # Find the strongest lesson about this word
                related = [l for l in lessons if word in l.get("finding", "").lower()]
                if related:
                    best = max(related, key=lambda l: l.get("strength", 0))
                    hypotheses.append({
                        "id": f"freq_{word}",
                        "type": "exploitation",
                        "hypothesis": f"'{word}' appears in {count} lessons. Strongest: {best.get('finding', '')}. Focus more resources here.",
                        "action": {"focus_on": word, "evidence_count": count},
                        "evidence": f"{count} lessons mention '{word}'",
                        "confidence": min(0.9, 0.4 + count * 0.1),
                    })

        return hypotheses

    def _detect_stagnation(self, lessons: List[Dict]) -> List[Dict]:
        """Detect when the system stops improving — time to explore."""
        hypotheses = []

        # Check if lessons have been static (no new findings recently)
        recent = [l for l in lessons if l.get("strength", 0) > 0.8]
        old = [l for l in lessons if l.get("strength", 0) < 0.3]

        if len(old) > len(recent) * 2 and len(lessons) > 3:
            hypotheses.append({
                "id": "stagnation_alert",
                "type": "exploration",
                "hypothesis": f"Knowledge is stagnating: {len(old)} weak lessons vs {len(recent)} strong. Increase exploration — try completely new approaches.",
                "action": {"force_exploration": 0.5},
                "evidence": f"{len(old)} decaying lessons, system may be stuck",
                "confidence": 0.8,
            })

        return hypotheses

    def _cross_references(self, lessons: List[Dict], graph_summary: dict) -> List[Dict]:
        """Find connections between different domains of knowledge."""
        hypotheses = []

        # Look for lessons from different sources that mention similar things
        if len(lessons) < 2:
            return hypotheses

        for i, l1 in enumerate(lessons):
            for l2 in lessons[i+1:]:
                # Check if different sources found similar things
                f1 = l1.get("finding", "").lower()
                f2 = l2.get("finding", "").lower()
                t1 = l1.get("type", "")
                t2 = l2.get("type", "")

                if t1 != t2:  # Different domains
                    # Simple word overlap
                    words1 = set(w for w in f1.split() if len(w) > 4)
                    words2 = set(w for w in f2.split() if len(w) > 4)
                    overlap = words1 & words2

                    if len(overlap) >= 2:
                        hypotheses.append({
                            "id": f"cross_{t1}_{t2}",
                            "type": "cross_reference",
                            "hypothesis": f"Cross-domain pattern: {t1} and {t2} both mention {', '.join(list(overlap)[:3])}. Combining these signals may improve results.",
                            "action": {"combine": [t1, t2], "shared_concepts": list(overlap)},
                            "evidence": f"Overlap: {overlap}",
                            "confidence": min(0.7, 0.3 + len(overlap) * 0.1),
                        })

        return hypotheses[:3]

    def _find_contradictions(self, lessons: List[Dict]) -> List[Dict]:
        """Detect lessons that contradict each other."""
        hypotheses = []
        contradiction_words = {"avoid", "never", "worst", "bad", "rarely", "fails"}
        positive_words = {"best", "wins", "optimal", "always", "often", "works"}

        for i, l1 in enumerate(lessons):
            f1 = l1.get("finding", "").lower()
            for l2 in lessons[i+1:]:
                f2 = l2.get("finding", "").lower()

                # Check for same topic but opposite sentiment
                words1 = set(f1.split())
                words2 = set(f2.split())
                shared_topic = words1 & words2 - {"the", "and", "for", "with", "that", "this"}

                if len(shared_topic) >= 2:
                    l1_neg = bool(words1 & contradiction_words)
                    l2_neg = bool(words2 & contradiction_words)
                    l1_pos = bool(words1 & positive_words)
                    l2_pos = bool(words2 & positive_words)

                    if (l1_neg and l2_pos) or (l1_pos and l2_neg):
                        hypotheses.append({
                            "id": f"contradiction_{i}",
                            "type": "contradiction",
                            "hypothesis": f"Contradiction detected: '{f1[:50]}' vs '{f2[:50]}'. Need targeted experiment to resolve.",
                            "action": {"resolve_contradiction": True, "lessons": [f1[:80], f2[:80]]},
                            "evidence": "Opposite sentiment on same topic",
                            "confidence": 0.9,
                        })

        return hypotheses[:2]

    def _find_unexplored(self, lessons: List[Dict], graph_summary: dict) -> List[Dict]:
        """Find areas in the graph with few lessons — unexplored territory."""
        hypotheses = []

        if not graph_summary.get("groups"):
            return hypotheses

        # Find groups with nodes but no lessons
        lesson_topics = set(l.get("type", "") for l in lessons)
        for group, count in graph_summary.get("groups", {}).items():
            if group not in lesson_topics and count > 3:
                hypotheses.append({
                    "id": f"explore_{group}",
                    "type": "exploration",
                    "hypothesis": f"Group '{group}' has {count} entities but no lessons. This is unexplored territory — investigate.",
                    "action": {"explore_group": group},
                    "evidence": f"{count} entities, 0 lessons",
                    "confidence": 0.5,
                })

        return hypotheses[:2]

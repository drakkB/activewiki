"""
thinker.py — The brain of ActiveWiki. Generates testable hypotheses.
Stage 2: Think. This is what makes ActiveWiki different from everything else.

No LLM needed — pure pattern detection on accumulated data.
Optionally, plug in an LLM for deeper analysis.
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Callable


class HypothesisGenerator:
    """
    Analyzes wiki content and generates testable hypotheses.
    Works standalone (pattern matching) or with an LLM (deeper reasoning).
    """

    def __init__(self, min_confidence: float = 0.3, max_hypotheses: int = 10, llm_fn: Optional[Callable] = None):
        self.min_confidence = min_confidence
        self.max_hypotheses = max_hypotheses
        self.llm_fn = llm_fn  # Optional: function(prompt) -> str

    def generate(self, wiki_content: str = "", lessons: List[Dict] = None, graph_summary: dict = None) -> List[Dict]:
        """Generate hypotheses from all available knowledge."""
        lessons = lessons or []
        graph_summary = graph_summary or {}
        hypotheses = []

        # Strategy 1: Direct lesson exploitation (the simplest — use what you know)
        hypotheses.extend(self._exploit_strong_lessons(lessons))

        # Strategy 2: Pattern frequency analysis
        hypotheses.extend(self._frequency_patterns(lessons))

        # Strategy 3: Stagnation detection
        hypotheses.extend(self._detect_stagnation(lessons))

        # Strategy 4: Cross-reference insights
        hypotheses.extend(self._cross_references(lessons))

        # Strategy 5: Contradiction detection
        hypotheses.extend(self._find_contradictions(lessons))

        # Strategy 6: Unexplored areas from graph
        hypotheses.extend(self._find_unexplored(lessons, graph_summary))

        # Strategy 7: LLM-powered deep analysis (if available)
        if self.llm_fn and lessons:
            hypotheses.extend(self._llm_analysis(lessons, wiki_content))

        # Deduplicate by id
        seen = set()
        unique = []
        for h in hypotheses:
            if h["id"] not in seen:
                seen.add(h["id"])
                unique.append(h)

        # Sort by confidence, limit
        unique = sorted(unique, key=lambda x: -x.get("confidence", 0))
        return unique[:self.max_hypotheses]

    def _exploit_strong_lessons(self, lessons: List[Dict]) -> List[Dict]:
        """The simplest strategy: if we know something works, do more of it."""
        hypotheses = []

        for lesson in lessons:
            strength = lesson.get("strength", 1.0)
            confidence_label = lesson.get("confidence", "medium")
            finding = lesson.get("finding", "")

            if not finding:
                continue

            # Strong + high confidence = exploit
            if strength >= 0.7 and confidence_label == "high":
                hypotheses.append({
                    "id": f"exploit_{lesson.get('id', finding[:20])}",
                    "type": "exploitation",
                    "hypothesis": f"High-confidence lesson: '{finding}'. Double down on this approach.",
                    "action": {"exploit_lesson": finding, "strength": strength},
                    "evidence": f"Strength={strength:.2f}, confidence={confidence_label}",
                    "confidence": min(0.9, 0.5 + strength * 0.2),
                })

            # Weak lessons = maybe stop doing this
            elif strength < 0.4:
                hypotheses.append({
                    "id": f"abandon_{lesson.get('id', finding[:20])}",
                    "type": "avoidance",
                    "hypothesis": f"Weak lesson (strength={strength:.2f}): '{finding}'. Consider abandoning this approach.",
                    "action": {"avoid_lesson": finding, "strength": strength},
                    "evidence": f"Strength decayed to {strength:.2f}",
                    "confidence": 0.5,
                })

        return hypotheses

    def _frequency_patterns(self, lessons: List[Dict]) -> List[Dict]:
        """Find words/concepts that appear across multiple lessons."""
        hypotheses = []
        if len(lessons) < 2:
            return hypotheses

        # Count recurring words across ALL findings
        findings = [l.get("finding", "") for l in lessons if l.get("finding")]
        word_freq = Counter()
        for f in findings:
            # Count unique words per finding (not repeated within same finding)
            unique_words = set(w.lower() for w in f.split() if len(w) > 3)
            for word in unique_words:
                word_freq[word] += 1

        # Words appearing in 2+ different lessons are patterns
        for word, count in word_freq.most_common(5):
            if count >= 2:
                related = [l for l in lessons if word in l.get("finding", "").lower()]
                best = max(related, key=lambda l: l.get("strength", 0))
                hypotheses.append({
                    "id": f"freq_{word}",
                    "type": "pattern",
                    "hypothesis": f"'{word}' appears across {count} different lessons. Key finding: {best.get('finding', '')}",
                    "action": {"focus_on": word, "evidence_count": count},
                    "evidence": f"{count} lessons mention '{word}'",
                    "confidence": min(0.9, 0.3 + count * 0.15),
                })

        return hypotheses

    def _detect_stagnation(self, lessons: List[Dict]) -> List[Dict]:
        """Detect when knowledge stops growing — time to explore."""
        hypotheses = []

        if len(lessons) < 3:
            return hypotheses

        # Check strength distribution
        strengths = [l.get("strength", 1.0) for l in lessons]
        avg_strength = sum(strengths) / len(strengths)
        weak = sum(1 for s in strengths if s < 0.5)
        strong = sum(1 for s in strengths if s >= 0.7)

        if weak > strong and avg_strength < 0.6:
            hypotheses.append({
                "id": "stagnation_alert",
                "type": "exploration",
                "hypothesis": f"Knowledge is decaying: avg strength={avg_strength:.2f}, {weak} weak vs {strong} strong lessons. Try completely new approaches.",
                "action": {"force_exploration": 0.5},
                "evidence": f"avg_strength={avg_strength:.2f}",
                "confidence": 0.8,
            })

        return hypotheses

    def _cross_references(self, lessons: List[Dict]) -> List[Dict]:
        """Find connections between lessons from different domains."""
        hypotheses = []

        if len(lessons) < 2:
            return hypotheses

        for i, l1 in enumerate(lessons):
            for l2 in lessons[i+1:]:
                t1 = l1.get("type", "general")
                t2 = l2.get("type", "general")
                if t1 == t2:
                    continue  # Same domain, skip

                f1 = set(w.lower() for w in l1.get("finding", "").split() if len(w) > 3)
                f2 = set(w.lower() for w in l2.get("finding", "").split() if len(w) > 3)
                overlap = f1 & f2 - {"that", "this", "with", "from", "have", "been", "most", "more"}

                if len(overlap) >= 2:
                    hypotheses.append({
                        "id": f"cross_{t1}_{t2}",
                        "type": "cross_reference",
                        "hypothesis": f"Cross-domain link: '{t1}' and '{t2}' share concepts {list(overlap)[:3]}. Combining these may yield better results.",
                        "action": {"combine": [t1, t2], "shared": list(overlap)},
                        "evidence": f"Shared: {overlap}",
                        "confidence": min(0.7, 0.3 + len(overlap) * 0.1),
                    })

        return hypotheses[:3]

    def _find_contradictions(self, lessons: List[Dict]) -> List[Dict]:
        """Detect lessons that might contradict each other."""
        hypotheses = []
        neg_words = {"avoid", "never", "worst", "bad", "rarely", "fails", "not", "don't"}
        pos_words = {"best", "wins", "optimal", "always", "often", "works", "good", "produces"}

        for i, l1 in enumerate(lessons):
            f1 = l1.get("finding", "").lower()
            w1 = set(f1.split())

            for l2 in lessons[i+1:]:
                f2 = l2.get("finding", "").lower()
                w2 = set(f2.split())

                # Same topic?
                shared = w1 & w2 - {"the", "and", "for", "with", "that", "this", "are", "was", "has"}
                if len(shared) < 2:
                    continue

                # Opposite sentiment?
                l1_pos = bool(w1 & pos_words)
                l1_neg = bool(w1 & neg_words)
                l2_pos = bool(w2 & pos_words)
                l2_neg = bool(w2 & neg_words)

                if (l1_pos and l2_neg) or (l1_neg and l2_pos):
                    hypotheses.append({
                        "id": f"contradiction_{i}",
                        "type": "contradiction",
                        "hypothesis": f"CONTRADICTION: '{f1[:60]}' vs '{f2[:60]}'. Run targeted experiment to resolve.",
                        "action": {"resolve": True, "lessons": [f1[:80], f2[:80]]},
                        "evidence": "Opposite sentiment on shared topic",
                        "confidence": 0.9,
                    })

        return hypotheses[:2]

    def _find_unexplored(self, lessons: List[Dict], graph_summary: dict) -> List[Dict]:
        """Find graph areas with no lessons — unexplored territory."""
        hypotheses = []
        if not graph_summary.get("groups"):
            return hypotheses

        lesson_types = set(l.get("type", "") for l in lessons)
        for group, count in graph_summary.get("groups", {}).items():
            if group not in lesson_types and count > 2:
                hypotheses.append({
                    "id": f"explore_{group}",
                    "type": "exploration",
                    "hypothesis": f"Graph group '{group}' has {count} entities but no lessons yet. Investigate this area.",
                    "action": {"explore_group": group},
                    "evidence": f"{count} entities, 0 lessons",
                    "confidence": 0.5,
                })

        return hypotheses[:2]

    def _llm_analysis(self, lessons: List[Dict], wiki_content: str) -> List[Dict]:
        """Use an LLM for deeper hypothesis generation (optional)."""
        if not self.llm_fn:
            return []

        prompt = f"""You are a research scientist analyzing accumulated knowledge.

LESSONS LEARNED:
{chr(10).join(f'- [{l.get("type","?")}] {l.get("finding","")} (strength={l.get("strength",1.0):.1f})' for l in lessons[:10])}

Generate 3 testable hypotheses in this JSON format:
[{{"id":"llm_1","type":"llm_insight","hypothesis":"description","action":{{"key":"value"}},"evidence":"why","confidence":0.6}}]

Return ONLY valid JSON array."""

        try:
            raw = self.llm_fn(prompt)
            import json
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        return []

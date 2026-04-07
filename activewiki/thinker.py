"""
thinker.py — The brain of ActiveWiki. Generates testable hypotheses.
Stage 2: Think. This is what makes ActiveWiki different from everything else.

No LLM needed — pure pattern detection on accumulated data.
Optionally, plug in an LLM for deeper analysis.
"""

import re
from collections import Counter
from datetime import datetime, timezone
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

        # Strategy 7: Temporal patterns (Grok suggestion)
        hypotheses.extend(self._detect_temporal_patterns(lessons))

        # Strategy 8: Non-obvious correlations (Grok suggestion)
        hypotheses.extend(self._find_non_obvious_correlations(lessons))

        # Strategy 9: Meta-learning (the wiki improves itself)
        hypotheses.extend(self._generate_meta_hypotheses(lessons))

        # Strategy 10: Hypothesis evolution (evolve old hypotheses into v2.0)
        hypotheses.extend(self._evolve_previous_hypotheses(lessons))

        # Strategy 11: Counterfactual simulation (what if we did the OPPOSITE?)
        hypotheses.extend(self._simulate_counterfactuals(lessons))

        # Strategy 12: LLM-powered deep analysis (if available)
        if self.llm_fn and lessons:
            hypotheses.extend(self._llm_analysis(lessons, wiki_content))

        # Deduplicate by id
        seen = set()
        unique = []
        for h in hypotheses:
            if h["id"] not in seen:
                seen.add(h["id"])
                unique.append(h)

        # Calculate expected impact for each hypothesis
        for h in unique:
            h["expected_impact"] = self._calculate_expected_impact(h, lessons)

        # Sort by expected impact (not just confidence)
        unique = sorted(unique, key=lambda x: -x.get("expected_impact", 0))
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

    def _detect_temporal_patterns(self, lessons: List[Dict]) -> List[Dict]:
        """Detect temporal patterns: recurring cycles, peak days."""
        hypotheses = []
        if len(lessons) < 5:
            return hypotheses

        dates = []
        for lesson in lessons:
            try:
                dt = datetime.fromisoformat(lesson.get("created", "").replace("Z", "+00:00"))
                dates.append((dt, lesson.get("strength", 1.0), lesson.get("finding", "")))
            except:
                continue

        if len(dates) < 3:
            return hypotheses

        # Detect weekly cycle
        day_freq = Counter(d[0].weekday() for d in dates)
        most_common = day_freq.most_common(1)[0]
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        if most_common[1] >= 3:
            hypotheses.append({
                "id": "temporal_cycle",
                "type": "temporal",
                "hypothesis": f"Temporal pattern: strongest lessons appear on {day_names[most_common[0]]}s ({most_common[1]} occurrences). Schedule experiments on this day.",
                "action": {"test_on_weekday": most_common[0]},
                "evidence": f"{most_common[1]} lessons created on {day_names[most_common[0]]}",
                "confidence": min(0.8, 0.4 + most_common[1] * 0.1),
            })

        return hypotheses

    def _find_non_obvious_correlations(self, lessons: List[Dict]) -> List[Dict]:
        """Find non-obvious correlations: co-occurring keywords with temporal lag."""
        hypotheses = []
        if len(lessons) < 4:
            return hypotheses

        events = []
        for lesson in lessons:
            words = set(w.lower() for w in lesson.get("finding", "").split() if len(w) > 4)
            events.append((words, lesson.get("strength", 1.0), lesson.get("created", "")))

        for i, (words1, s1, d1) in enumerate(events):
            for j, (words2, s2, d2) in enumerate(events):
                if i >= j:
                    continue
                overlap = words1 & words2
                if len(overlap) >= 2 and min(s1, s2) > 0.6:
                    # Temporal lag
                    try:
                        dt1 = datetime.fromisoformat(d1.replace("Z", "+00:00"))
                        dt2 = datetime.fromisoformat(d2.replace("Z", "+00:00"))
                        lag_days = abs((dt2 - dt1).days)
                    except:
                        lag_days = 0

                    hypotheses.append({
                        "id": f"corr_{'_'.join(sorted(list(overlap))[:2])}",
                        "type": "correlation",
                        "hypothesis": f"Non-obvious correlation: {list(overlap)[:3]} appear together (strength {min(s1,s2):.2f}, lag {lag_days}d). Test causality.",
                        "action": {"test_correlation": list(overlap)[:3], "lag_days": lag_days},
                        "evidence": f"overlap={list(overlap)[:3]}, lag={lag_days}d",
                        "confidence": min(0.85, 0.4 + len(overlap) * 0.1),
                    })

        return hypotheses[:4]

    def _generate_meta_hypotheses(self, lessons: List[Dict]) -> List[Dict]:
        """Meta-learning: the wiki generates ideas to improve ITSELF."""
        if len(lessons) < 5:
            return []

        total = len(lessons)
        strong = sum(1 for l in lessons if l.get("strength", 0) > 0.7)
        success_rate = strong / total

        hypotheses = []

        if success_rate < 0.4:
            hypotheses.append({
                "id": "meta_low_success",
                "type": "meta",
                "hypothesis": f"Wiki success rate is low ({success_rate:.0%}). Only {strong}/{total} lessons are strong. Increase exploration or change decay_rate.",
                "action": {"meta_action": "tune_decay", "current_success_rate": success_rate},
                "evidence": f"{total} lessons, {strong} strong ({success_rate:.0%})",
                "confidence": 0.85,
            })
        elif success_rate > 0.8:
            hypotheses.append({
                "id": "meta_high_success",
                "type": "meta",
                "hypothesis": f"Wiki success rate is high ({success_rate:.0%}). Increase hypothesis count per cycle to discover more.",
                "action": {"meta_action": "increase_hypotheses", "current_success_rate": success_rate},
                "evidence": f"{total} lessons, {strong} strong ({success_rate:.0%})",
                "confidence": 0.7,
            })

        return hypotheses

    def _calculate_expected_impact(self, hypothesis: Dict, lessons: List[Dict]) -> float:
        """Expected impact score (ROI-like) for prioritizing hypotheses."""
        confidence = hypothesis.get("confidence", 0.5)

        # Action value multiplier based on type
        action_value = 1.0
        h_type = hypothesis.get("type", "")
        if h_type == "correlation":
            action_value = 1.8
        elif h_type == "temporal":
            action_value = 1.4
        elif h_type == "exploitation":
            action_value = 1.6
        elif h_type == "contradiction":
            action_value = 2.0  # Resolving contradictions = highest value
        elif h_type == "meta":
            action_value = 2.2  # Improving the system itself = max value

        # Bonus for supporting lessons
        hyp_words = set(hypothesis.get("hypothesis", "").lower().split()[-5:])
        supporting = sum(1 for l in lessons
                        if any(w in l.get("finding", "").lower() for w in hyp_words if len(w) > 4))

        impact = confidence * action_value * (1 + min(supporting * 0.15, 1.0))
        return round(min(impact, 9.9), 2)

    def _evolve_previous_hypotheses(self, lessons: List[Dict]) -> List[Dict]:
        """Hypothesis evolution: take old validated lessons and create v2.0 variants."""
        hypotheses = []
        for lesson in lessons:
            strength = lesson.get("strength", 0)
            confirmations = lesson.get("confirmations", 0)
            finding = lesson.get("finding", "")

            # Only evolve lessons that were confirmed but could be better
            if strength > 0.6 and confirmations >= 2 and finding:
                hypotheses.append({
                    "id": f"evolve_{lesson.get('id', 'old')}",
                    "type": "evolution",
                    "hypothesis": f"Evolve validated lesson: '{finding[:60]}' — test a stronger variant with more data or tighter parameters.",
                    "action": {"evolve_hypothesis": lesson.get("id"), "original_strength": strength},
                    "evidence": f"Strength={strength:.2f}, confirmed {confirmations}x — ready for v2.0",
                    "confidence": min(0.85, 0.5 + confirmations * 0.1),
                })
        return hypotheses[:3]

    def _simulate_counterfactuals(self, lessons: List[Dict]) -> List[Dict]:
        """Counterfactual simulation: what if we did the OPPOSITE of our strongest lessons?"""
        hypotheses = []
        if len(lessons) < 6:
            return hypotheses

        # Take the strongest lessons and challenge them
        high_strength = [l for l in lessons if l.get("strength", 0) > 0.8]
        for lesson in high_strength[:3]:
            finding = lesson.get("finding", "")
            hypotheses.append({
                "id": f"counter_{lesson.get('id', 'x')}",
                "type": "counterfactual",
                "hypothesis": f"COUNTERFACTUAL: What if '{finding[:50]}' is wrong? Test the radical opposite.",
                "action": {"counterfactual_test": True, "challenge_lesson": finding[:80]},
                "evidence": f"Challenging high-strength lesson (str={lesson.get('strength',0):.2f}) — real science questions everything",
                "confidence": 0.65,  # Lower confidence — it's a challenge, not a certainty
            })
        return hypotheses

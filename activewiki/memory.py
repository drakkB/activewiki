"""
memory.py — Decay + Consolidation + Confidence Scoring + Wiki Pruning.
Inspired by elfmem: old knowledge fades, confirmed knowledge strengthens.
Enhanced with Grok's suggestions: confidence_score evolves with age/confirmations,
and intelligent pruning keeps the wiki lean without losing critical knowledge.
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

    def _update_confidence_score(self, lesson: Dict):
        """Evolving confidence score 0-1 based on strength, confirmations, and age."""
        confirmations = lesson.get("confirmations", 0)
        strength = lesson.get("strength", 1.0)

        try:
            updated = datetime.fromisoformat(lesson.get("updated", "").replace("Z", "+00:00"))
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_old = (datetime.now(timezone.utc) - updated).total_seconds() / 86400
        except:
            days_old = 0

        # Formula: strength (60%) + confirmations (30%) + age penalty (10%)
        base = (strength * 0.6) + (min(confirmations, 10) / 10 * 0.3)
        age_penalty = max(0.1, 1 - (days_old * 0.02))  # -2% per day since last update
        lesson["confidence_score"] = round(max(0.1, min(1.0, base * age_penalty)), 3)

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
                self._update_confidence_score(lesson)
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

            self._update_confidence_score(lesson)

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

    def crystallize_knowledge(self) -> int:
        """
        Knowledge Crystallization: when 3+ lessons say similar things,
        merge them into a higher-level 'meta-lesson'. The wiki rises in abstraction.
        """
        created = 0
        clusters = {}

        for lesson in self.lessons:
            if lesson.get("type") == "crystallized":
                continue  # Don't re-crystallize
            # Cluster by shared key words
            key_words = sorted(w.lower() for w in lesson.get("finding", "").split() if len(w) > 4)
            key = " ".join(key_words[:5])
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(lesson)

        for key, group in clusters.items():
            if len(group) >= 3 and all(l.get("strength", 0) > 0.6 for l in group):
                avg_strength = sum(l.get("strength", 0) for l in group) / len(group)
                meta_finding = f"CRYSTALLIZED ({len(group)} lessons): {group[0].get('finding', '')[:60]}"

                self.lessons.append({
                    "id": f"crystal_{len(self.lessons)}",
                    "finding": meta_finding,
                    "type": "crystallized",
                    "confidence": "very_high",
                    "strength": min(2.0, avg_strength * 1.3),
                    "confirmations": len(group),
                    "confidence_score": 0.9,
                    "created": datetime.now(timezone.utc).isoformat(),
                    "updated": datetime.now(timezone.utc).isoformat(),
                    "crystallized_from": [l.get("id", "") for l in group],
                })
                created += 1

                # Boost the original lessons slightly
                for l in group:
                    l["strength"] = min(2.0, l.get("strength", 1.0) + 0.1)

        if created:
            self._save()
        return created

    def prune_wiki(self, wiki_dir: Path, max_pages: int = 150) -> int:
        """
        Intelligent wiki pruning: keeps the wiki lean without losing critical knowledge.
        Pages linked to high-confidence lessons are protected. Weakest pages removed first.
        """
        md_files = [f for f in Path(wiki_dir).glob("*.md") if f.name != "index.md"]
        if len(md_files) <= max_pages:
            return 0

        # Critical lessons (high confidence + high strength)
        critical = [l for l in self.lessons
                    if l.get("confidence_score", 0) > 0.7 and l.get("strength", 0) > 0.7]

        # Score each page
        scored = []
        for f in md_files:
            content = f.read_text()[:2000].lower()
            # Score = how many critical lessons reference this page
            crit_score = sum(1 for l in critical if l.get("finding", "")[:30].lower() in content)
            size_score = len(content) / 1000  # bigger pages = more valuable
            scored.append((f, crit_score + size_score))

        # Sort weakest first, delete until under max_pages
        scored.sort(key=lambda x: x[1])
        to_delete = len(scored) - max_pages
        deleted = 0

        for f, score in scored[:to_delete]:
            # Never delete pages with critical lessons
            if score > 0:
                continue
            f.unlink()
            deleted += 1

        return deleted

    @staticmethod
    def _similar(text1: str, text2: str) -> bool:
        """Simple similarity check between two findings."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.4

"""
compiler.py — Compiles raw data into structured Markdown wiki pages.
Stage 1 of ActiveWiki: Accumulate.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class WikiCompiler:
    """Compiles raw JSON data into structured Markdown wiki pages."""

    def __init__(self, raw_dir: Path, wiki_dir: Path):
        self.raw_dir = raw_dir
        self.wiki_dir = wiki_dir

    def compile(self, data: dict, source_name: str = "unknown") -> dict:
        """
        Compile raw data dict into Markdown wiki pages.
        Extracts entities, relationships, and key findings.
        """
        entities = []
        relationships = []
        pages_written = 0
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        # Auto-detect data structure and compile accordingly
        if isinstance(data, dict):
            # Extract top-level keys as potential entities
            for key, value in data.items():
                entity_id = self._make_id(key)
                entities.append({
                    "id": entity_id,
                    "label": key,
                    "group": self._detect_group(key, value),
                    "source": source_name,
                })

                # Write wiki page for significant entries
                if isinstance(value, (dict, list)) and len(str(value)) > 100:
                    md = self._compile_entry(key, value, timestamp, source_name)
                    page_file = self.wiki_dir / f"{entity_id}.md"
                    page_file.write_text(md)
                    pages_written += 1

                # Detect relationships
                if isinstance(value, dict):
                    for sub_key in value:
                        if sub_key in data:
                            relationships.append({
                                "source": entity_id,
                                "target": self._make_id(sub_key),
                                "type": "references",
                            })

        # Update index
        self._update_index(entities, timestamp)

        return {
            "entities": entities,
            "relationships": relationships,
            "pages_written": pages_written,
            "timestamp": timestamp,
        }

    def _compile_entry(self, key: str, value, timestamp: str, source: str) -> str:
        """Compile a single entry into Markdown."""
        md = f"# {key}\n\n"
        md += f"*Compiled: {timestamp} | Source: {source}*\n\n"

        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, (str, int, float, bool)):
                    md += f"- **{k}**: {v}\n"
                elif isinstance(v, list) and len(v) <= 10:
                    md += f"- **{k}**: {', '.join(str(x) for x in v)}\n"
                elif isinstance(v, dict):
                    md += f"\n## {k}\n\n"
                    for kk, vv in v.items():
                        md += f"- {kk}: {str(vv)[:200]}\n"
        elif isinstance(value, list):
            for i, item in enumerate(value[:20]):
                if isinstance(item, dict):
                    md += f"\n### Entry {i+1}\n"
                    for k, v in item.items():
                        md += f"- {k}: {str(v)[:200]}\n"
                else:
                    md += f"- {item}\n"

        return md

    def _update_index(self, entities: list, timestamp: str):
        """Update the wiki index page."""
        index_file = self.wiki_dir / "index.md"
        existing = ""
        if index_file.exists():
            existing = index_file.read_text()

        new_entries = ""
        for e in entities:
            link = f"- [{e['label']}]({e['id']}.md) — {e.get('group', 'general')}\n"
            if link not in existing:
                new_entries += link

        if new_entries:
            if not existing:
                existing = f"# ActiveWiki Index\n\n*Last updated: {timestamp}*\n\n"
            existing += new_entries
            index_file.write_text(existing)

    def load_all(self) -> str:
        """Load all wiki pages into a single context string."""
        content = ""
        for f in sorted(self.wiki_dir.glob("*.md")):
            content += f.read_text() + "\n\n---\n\n"
        return content

    def search(self, query: str) -> List[Dict]:
        """Simple keyword search across wiki pages."""
        results = []
        query_lower = query.lower()
        for f in self.wiki_dir.glob("*.md"):
            text = f.read_text()
            if query_lower in text.lower():
                # Find matching lines
                matches = [line.strip() for line in text.split("\n")
                          if query_lower in line.lower()]
                results.append({
                    "page": f.stem,
                    "matches": matches[:5],
                    "relevance": text.lower().count(query_lower),
                })
        return sorted(results, key=lambda x: -x["relevance"])

    @staticmethod
    def _make_id(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")

    @staticmethod
    def _detect_group(key: str, value) -> str:
        key_lower = key.lower()
        if any(w in key_lower for w in ["strategy", "trading", "bot"]):
            return "strategy"
        if any(w in key_lower for w in ["engine", "cron", "evolution"]):
            return "engine"
        if any(w in key_lower for w in ["result", "metric", "score"]):
            return "metric"
        if any(w in key_lower for w in ["config", "param", "setting"]):
            return "config"
        return "general"

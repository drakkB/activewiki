"""
graph.py — Knowledge Graph for entity relationships.
Tracks how concepts, findings, and actions are connected.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter


class KnowledgeGraph:
    """Lightweight knowledge graph stored as JSON. No external DB needed."""

    def __init__(self, graph_file: Path):
        self.graph_file = Path(graph_file)
        self.nodes = {}
        self.edges = []
        self._load()

    def _load(self):
        if self.graph_file.exists():
            try:
                data = json.loads(self.graph_file.read_text())
                self.nodes = {n["id"]: n for n in data.get("nodes", [])}
                self.edges = data.get("edges", [])
            except:
                pass

    def _save(self):
        data = {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "meta": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "groups": dict(Counter(n.get("group", "general") for n in self.nodes.values())),
            }
        }
        self.graph_file.write_text(json.dumps(data, indent=2, default=str))

    def add_node(self, node_id: str, label: str, group: str = "general", meta: dict = None):
        """Add or update a node."""
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "group": group,
            "meta": meta or {},
        }
        self._save()

    def add_edge(self, source: str, target: str, rel_type: str = "related", weight: float = 1.0):
        """Add a relationship between two nodes."""
        # Avoid duplicates
        for e in self.edges:
            if e["source"] == source and e["target"] == target and e["rel"] == rel_type:
                return
        self.edges.append({"source": source, "target": target, "rel": rel_type, "weight": weight})
        self._save()

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """Get connected nodes up to N hops away."""
        neighbors = set()
        current = {node_id}
        for _ in range(depth):
            next_level = set()
            for e in self.edges:
                if e["source"] in current:
                    next_level.add(e["target"])
                if e["target"] in current:
                    next_level.add(e["source"])
            neighbors.update(next_level)
            current = next_level
        neighbors.discard(node_id)
        return list(neighbors)

    def get_summary(self) -> dict:
        """Get a summary of the graph for the thinker."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "groups": dict(Counter(n.get("group", "general") for n in self.nodes.values())),
            "top_connected": sorted(
                [(nid, sum(1 for e in self.edges if e["source"] == nid or e["target"] == nid))
                 for nid in self.nodes],
                key=lambda x: -x[1]
            )[:10],
        }

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

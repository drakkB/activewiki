"""
wiki.py — Main ActiveWiki class. Orchestrates the 5-stage loop:
Accumulate → Think → Act → Learn → Repeat
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from .compiler import WikiCompiler
from .thinker import HypothesisGenerator
from .memory import MemoryManager
from .graph import KnowledgeGraph


class ActiveWiki:
    """
    The wiki that thinks, acts, and learns.

    Usage:
        wiki = ActiveWiki(working_dir="./my_wiki")
        wiki.ingest("data.json")
        hypotheses = wiki.think()
        results = wiki.act(hypotheses, engine=my_engine)
        wiki.learn(results)
    """

    def __init__(
        self,
        working_dir: str = "./activewiki_data",
        decay_rate: float = 0.05,
        consolidation_boost: float = 0.1,
        min_confidence: float = 0.3,
        max_hypotheses: int = 10,
    ):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Sub-directories
        self.raw_dir = self.working_dir / "raw"
        self.wiki_dir = self.working_dir / "wiki"
        self.results_dir = self.working_dir / "results"
        self.raw_dir.mkdir(exist_ok=True)
        self.wiki_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

        # Config
        self.decay_rate = decay_rate
        self.consolidation_boost = consolidation_boost
        self.min_confidence = min_confidence
        self.max_hypotheses = max_hypotheses

        # Components
        self.compiler = WikiCompiler(self.raw_dir, self.wiki_dir)
        self.thinker = HypothesisGenerator(min_confidence=min_confidence, max_hypotheses=max_hypotheses)
        self.memory = MemoryManager(self.working_dir, decay_rate=decay_rate, consolidation_boost=consolidation_boost)
        self.graph = KnowledgeGraph(self.working_dir / "graph.json")

        # State
        self.state_file = self.working_dir / "state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "total_ingestions": 0,
            "total_hypotheses": 0,
            "total_actions": 0,
            "total_learnings": 0,
            "total_loops": 0,
            "created": datetime.now(timezone.utc).isoformat(),
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str))

    # ═══════════════════════════════════════════════════════════
    # STAGE 1: ACCUMULATE
    # ═══════════════════════════════════════════════════════════

    def ingest(self, data_source: str, data: dict = None) -> dict:
        """
        Ingest raw data into the wiki.
        data_source: path to JSON file, or a name for the data
        data: optional dict (if not loading from file)
        """
        if data is None:
            path = Path(data_source)
            if path.exists():
                data = json.loads(path.read_text())
            else:
                return {"error": f"File not found: {data_source}"}

        # Save raw
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        raw_file = self.raw_dir / f"{timestamp}_{Path(data_source).stem}.json"
        raw_file.write_text(json.dumps(data, indent=2, default=str))

        # Compile into wiki
        compiled = self.compiler.compile(data, source_name=data_source)

        # Update graph
        if compiled.get("entities"):
            for entity in compiled["entities"]:
                self.graph.add_node(entity["id"], entity.get("label", entity["id"]), entity.get("group", "general"))
            for rel in compiled.get("relationships", []):
                self.graph.add_edge(rel["source"], rel["target"], rel.get("type", "related"))

        self.state["total_ingestions"] = self.state.get("total_ingestions", 0) + 1
        self._save_state()

        return {
            "raw_file": str(raw_file),
            "wiki_pages": compiled.get("pages_written", 0),
            "entities": len(compiled.get("entities", [])),
            "relationships": len(compiled.get("relationships", [])),
        }

    # ═══════════════════════════════════════════════════════════
    # STAGE 2: THINK
    # ═══════════════════════════════════════════════════════════

    def think(self) -> List[Dict]:
        """
        Analyze accumulated wiki knowledge and generate testable hypotheses.
        Returns a list of hypothesis dicts with confidence scores.
        """
        # Load all wiki content
        wiki_content = self.compiler.load_all()
        lessons = self.memory.get_active_lessons()
        graph_data = self.graph.get_summary()

        # Generate hypotheses
        hypotheses = self.thinker.generate(
            wiki_content=wiki_content,
            lessons=lessons,
            graph_summary=graph_data,
        )

        self.state["total_hypotheses"] = self.state.get("total_hypotheses", 0) + len(hypotheses)
        self._save_state()

        # Save hypotheses
        hyp_file = self.working_dir / "hypotheses.json"
        hyp_file.write_text(json.dumps({
            "hypotheses": hypotheses,
            "generated": datetime.now(timezone.utc).isoformat(),
            "count": len(hypotheses),
        }, indent=2, default=str))

        return hypotheses

    # ═══════════════════════════════════════════════════════════
    # STAGE 3: ACT
    # ═══════════════════════════════════════════════════════════

    def act(self, hypotheses: List[Dict], engine: Any = None) -> List[Dict]:
        """
        Send hypotheses to an execution engine for testing.
        engine: any object with an execute(hypothesis) method.
        Returns results.
        """
        if engine is None:
            return [{"hypothesis": h, "result": "no_engine", "success": None} for h in hypotheses]

        results = []
        for h in hypotheses:
            if h.get("confidence", 0) < self.min_confidence:
                continue
            try:
                result = engine.execute(h)
                results.append({
                    "hypothesis": h,
                    "result": result,
                    "success": result.get("success", None) if isinstance(result, dict) else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                results.append({
                    "hypothesis": h,
                    "result": {"error": str(e)},
                    "success": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        self.state["total_actions"] = self.state.get("total_actions", 0) + len(results)
        self._save_state()

        # Save results
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"results_{timestamp}.json"
        results_file.write_text(json.dumps(results, indent=2, default=str))

        return results

    # ═══════════════════════════════════════════════════════════
    # STAGE 4: LEARN
    # ═══════════════════════════════════════════════════════════

    def learn(self, results: List[Dict]) -> dict:
        """
        Process results and update the wiki.
        Successful hypotheses are consolidated, failed ones decay.
        """
        consolidated = 0
        decayed = 0

        for r in results:
            hypothesis = r.get("hypothesis", {})
            success = r.get("success")

            if success is True:
                # Consolidate: strengthen the lesson
                self.memory.consolidate(hypothesis, boost=self.consolidation_boost)
                consolidated += 1
                # Add to graph as validated knowledge
                self.graph.add_node(
                    f"validated_{hypothesis.get('id', 'unknown')}",
                    hypothesis.get("hypothesis", "")[:50],
                    "validated"
                )
            elif success is False:
                # Decay: weaken the lesson
                self.memory.decay_specific(hypothesis)
                decayed += 1

        # Apply general time-based decay to all lessons
        expired = self.memory.apply_decay()

        self.state["total_learnings"] = self.state.get("total_learnings", 0) + 1
        self._save_state()

        return {
            "consolidated": consolidated,
            "decayed": decayed,
            "expired_lessons": expired,
        }

    # ═══════════════════════════════════════════════════════════
    # STAGE 5: LOOP
    # ═══════════════════════════════════════════════════════════

    def run_loop(self, engine: Any = None, data_source: str = None, interval: str = "nightly"):
        """
        Run the full Accumulate → Think → Act → Learn loop once.
        For continuous operation, call this from a cron or scheduler.
        """
        print(f"[ActiveWiki] Loop #{self.state.get('total_loops', 0) + 1}")

        # 1. Accumulate (if new data)
        if data_source:
            ingested = self.ingest(data_source)
            print(f"  Accumulated: {ingested}")

        # 2. Think
        hypotheses = self.think()
        print(f"  Generated: {len(hypotheses)} hypotheses")

        # 3. Act
        results = self.act(hypotheses, engine=engine)
        acted = [r for r in results if r.get("success") is not None]
        print(f"  Acted on: {len(acted)} hypotheses")

        # 4. Learn
        learned = self.learn(results)
        print(f"  Learned: {learned['consolidated']} consolidated, {learned['decayed']} decayed")

        self.state["total_loops"] = self.state.get("total_loops", 0) + 1
        self._save_state()

        return {
            "hypotheses": len(hypotheses),
            "actions": len(acted),
            "consolidated": learned["consolidated"],
            "decayed": learned["decayed"],
            "loop": self.state["total_loops"],
        }

    # ═══════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════

    def status(self) -> dict:
        """Get current wiki status."""
        return {
            **self.state,
            "wiki_pages": len(list(self.wiki_dir.glob("*.md"))),
            "raw_files": len(list(self.raw_dir.glob("*.json"))),
            "result_files": len(list(self.results_dir.glob("*.json"))),
            "graph_nodes": self.graph.node_count(),
            "graph_edges": self.graph.edge_count(),
            "active_lessons": len(self.memory.get_active_lessons()),
        }

    def search(self, query: str) -> List[Dict]:
        """Search the wiki for relevant knowledge."""
        return self.compiler.search(query)

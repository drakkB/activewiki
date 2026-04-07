"""
ActiveWiki — The wiki that thinks, acts, and learns.
A closed-loop knowledge framework where knowledge generates actions,
and actions generate knowledge.

Usage:
    from activewiki import ActiveWiki

    wiki = ActiveWiki(working_dir="./my_wiki")
    wiki.ingest("data.json")
    hypotheses = wiki.think()
    results = wiki.act(hypotheses, engine=my_engine)
    wiki.learn(results)
"""

from .wiki import ActiveWiki
from .compiler import WikiCompiler
from .thinker import HypothesisGenerator
from .memory import MemoryManager
from .graph import KnowledgeGraph

__version__ = "0.1.0"
__author__ = "Strategy Arena Team"
__all__ = ["ActiveWiki", "WikiCompiler", "HypothesisGenerator", "MemoryManager", "KnowledgeGraph"]

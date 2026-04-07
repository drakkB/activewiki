# ActiveWiki

**The first wiki that does science on its own.**

> RAG retrieves documents. MemPalace organizes memory. ActiveWiki runs experiments.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

**MemPalace = persistent memory. ActiveWiki = persistent intelligence.**

You don't read your wiki. Your wiki reads the world, tests ideas, and makes you smarter.

---

## The Problem

| Tool | Stores | Organizes | Compresses | Generates hypotheses | Executes & learns | Closed loop |
|------|--------|-----------|------------|---------------------|-------------------|-------------|
| **RAG** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Karpathy Wiki** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **MemPalace** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **ActiveWiki** | ✓ | ✓ | ✓ | **✓** | **✓** | **✓** |

Every knowledge system stops at storage. ActiveWiki is the first framework where **knowledge generates actions, and actions generate knowledge** — in a continuous autonomous loop.

```
Data → Compile → Wiki → Hypotheses → Execute → Results → Wiki (updated)
  ↑                                                              ↓
  └──────────────────── CLOSED LOOP ────────────────────────────┘
```

## How It Works

ActiveWiki has 5 stages that run in a loop:

### 1. Accumulate
Raw data (logs, experiments, API responses, metrics) is compiled into structured Markdown wiki pages. Like Karpathy's pattern — but this is just the beginning.

```python
from activewiki import ActiveWiki

wiki = ActiveWiki(working_dir="./my_wiki")
wiki.ingest("experiments/results_tonight.json")
# → Compiles into structured .md pages with cross-references
```

### 2. Think
The wiki analyzes its own content and generates **testable hypotheses**. It detects patterns, correlations, anomalies, and contradictions across all accumulated knowledge.

```python
hypotheses = wiki.think()
# → [
#   {"hypothesis": "Parameter X works best when condition Y is true",
#    "evidence": "3 out of 4 experiments confirm this",
#    "confidence": 0.75,
#    "action": {"set_param_x": 42}},
#   ...
# ]
```

### 3. Act
Hypotheses are sent to an execution engine. ActiveWiki doesn't care what the engine is — it could be a trading bot, a CI/CD pipeline, a research experiment, or a code optimizer.

```python
wiki.act(hypotheses, engine=my_execution_engine)
# → Engine runs the hypotheses as experiments
```

### 4. Learn
Results come back. The wiki updates itself: successful hypotheses are **consolidated** (strength increases), failed ones **decay** (strength decreases over time). Contradictions are flagged.

```python
wiki.learn(results)
# → Wiki pages updated with new evidence
# → Successful patterns strengthened
# → Failed patterns weakened (elfmem decay)
# → Contradictions detected and flagged
```

### 5. Repeat
The loop runs autonomously. Every cycle, the wiki gets smarter. Knowledge compounds.

```python
wiki.run_loop(interval="nightly")  # or "hourly", "on_new_data", etc.
```

## What Makes This Different

| Feature | RAG | Karpathy Wiki | MemPalace | **ActiveWiki** |
|---------|-----|--------------|-----------|---------------|
| Stores knowledge | ✓ | ✓ | ✓ | ✓ |
| Structured storage | ✗ | ✓ | ✓ | ✓ |
| Compression | ✗ | ✗ | ✓ (AAAK) | ✓ (pluggable) |
| Generates hypotheses | ✗ | ✗ | ✗ | **✓** |
| Executes actions | ✗ | ✗ | ✗ | **✓** |
| Learns from results | ✗ | ✗ | ✗ | **✓** |
| Decay + consolidation | ✗ | ✗ | ✗ | **✓** |
| Contradiction detection | ✗ | ✗ | ✓ | **✓** |
| Closed-loop autonomous | ✗ | ✗ | ✗ | **✓** |

## Use Cases

### Trading (Strategy Arena)
```
Nightly experiments → Wiki learns which RSI settings work →
Generates hypothesis "RSI 25 + Bollinger in BEAR" →
Darwin Engine tests it → Results: +3.2% →
Wiki consolidates: strength 0.6 → 0.8
```

### Code Quality
```
CI/CD logs → Wiki learns which tests fail often →
Generates hypothesis "Module X needs retry logic" →
Code agent implements fix → Results: 0 failures →
Wiki consolidates the pattern
```

### SEO Optimization
```
GSC data → Wiki learns which pages are thin →
Generates hypothesis "Page Y needs 200 more words" →
Content agent writes text → Results: CTR +40% →
Wiki consolidates what works
```

### Research
```
Papers ingested → Wiki detects conflicting findings →
Generates hypothesis "Method A > Method B when dataset > 10K" →
Researcher tests → Results confirm →
Wiki updates: Method A recommended for large datasets
```

## Installation

```bash
pip install activewiki
```

## Quick Start

```python
from activewiki import ActiveWiki

# Initialize
wiki = ActiveWiki(
    working_dir="./my_project_wiki",
    decay_rate=0.05,        # 5% strength decay per day
    consolidation_boost=0.1, # +10% strength when confirmed
    min_confidence=0.3,      # Don't act on low-confidence hypotheses
)

# Ingest data
wiki.ingest("data/experiment_results.json")

# Think: generate hypotheses
hypotheses = wiki.think()

# Act: send to your engine
results = wiki.act(hypotheses, engine=my_engine)

# Learn: update wiki with results
wiki.learn(results)

# Or run the full loop
wiki.run_loop(interval="nightly", engine=my_engine)
```

## Architecture

```
activewiki/
├── __init__.py          # Main ActiveWiki class
├── compiler.py          # Raw data → Markdown compiler
├── thinker.py           # Hypothesis generator (pattern detection)
├── actor.py             # Sends hypotheses to execution engines
├── learner.py           # Processes results, updates wiki
├── memory.py            # Decay + consolidation (elfmem-inspired)
├── graph.py             # Knowledge graph of entities + relationships
├── contradictions.py    # Detects conflicting knowledge
└── engines/
    ├── __init__.py
    ├── base.py          # Abstract engine interface
    ├── trading.py       # Trading strategy engine (example)
    ├── code.py          # Code quality engine (example)
    └── seo.py           # SEO optimization engine (example)
```

## The Philosophy

Every AI memory system asks: **"How do we store knowledge?"**

ActiveWiki asks a different question: **"How do we make knowledge act?"**

Storage is solved. Karpathy solved Markdown accumulation. Milla Jovovich solved spatial organization. The missing piece was always the same: **the feedback loop between knowing and doing.**

ActiveWiki is that feedback loop.

## Origin

Built by the team behind [Strategy Arena](https://strategyarena.io) — a platform where 59 AI trading strategies compete live on Bitcoin. We needed a knowledge system that didn't just record what worked, but actively proposed what to try next and learned from the results.

After implementing Karpathy's autoresearch pattern, LightRAG-inspired graph retrieval, MemPalace compression, and a Meta-Harness that optimizes the optimizer — we realized the real innovation wasn't any single piece. It was the **closed loop** connecting them all.

ActiveWiki is that loop, extracted into a reusable framework.

## Credits

Standing on the shoulders of:
- **Andrej Karpathy** — autoresearch pattern, LLM wiki concept
- **Milla Jovovich & Ben Sigman** — MemPalace, AAAK compression, palace architecture
- **HKUDS** — LightRAG, graph-augmented retrieval
- **Stanford** — Meta-Harness research
- **emson** — elfmem, adaptive memory with decay

## License

MIT License — use it, modify it, build on it.

---

*Knowledge that acts. Actions that teach. The loop that learns.*

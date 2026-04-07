#!/usr/bin/env python3
"""
Example: ActiveWiki for AI Trading Strategy Evolution

This example shows how ActiveWiki closes the loop:
1. Ingest nightly experiment results
2. Wiki generates hypotheses about what works
3. Hypotheses are tested by a trading engine
4. Results update the wiki — knowledge compounds

Based on Strategy Arena (strategyarena.io) where 59 AI strategies
compete live on Bitcoin with 9 nightly evolution engines.
"""

from activewiki import ActiveWiki


# A simple mock trading engine for demonstration
class TradingEngine:
    """Mock engine that tests trading hypotheses."""

    def execute(self, hypothesis: dict) -> dict:
        """Test a hypothesis by running a mini backtest."""
        action = hypothesis.get("action", {})

        # Simulate: hypotheses about RSI and Bollinger tend to work
        focus = action.get("focus_on", "")
        if focus in ("rsi", "bollinger", "momentum"):
            return {"success": True, "pnl": 2.3, "reason": f"{focus} confirmed profitable"}
        elif action.get("force_exploration"):
            return {"success": True, "pnl": 0.5, "reason": "exploration found new edge"}
        else:
            return {"success": False, "pnl": -0.8, "reason": "hypothesis not confirmed"}


def main():
    # Initialize
    wiki = ActiveWiki(
        working_dir="./trading_wiki",
        decay_rate=0.05,       # 5% decay per day
        consolidation_boost=0.15,
        min_confidence=0.3,
    )

    # ─── NIGHT 1: Ingest experiment results ───
    print("=" * 50)
    print("NIGHT 1: Ingesting experiment results")
    print("=" * 50)

    wiki.ingest("night_1", data={
        "darwin_engine": {
            "experiments": 1000,
            "improvements": 8,
            "best_fitness": 5.98,
            "best_params": {"entry_type": "rsi", "rsi_entry": 25, "stop_loss": 3.5},
        },
        "chimera": {
            "experiments": 500,
            "improvements": 4,
            "f1_score": 47.3,
            "precision": 42,
            "recall": 94,
        },
        "leviathan": {
            "experiments": 500,
            "improvements": 0,
            "best_metric": 57.53,
            "weights": {"chimera": 0.72, "regime": 1.24, "news": 1.25},
        },
    })

    # Add some lessons manually (normally done by the compiler)
    wiki.memory.add_lesson("RSI entry at 25 produces best results", "parameters", "high")
    wiki.memory.add_lesson("Bollinger bands win 3 out of 4 runs", "entry_type", "high")
    wiki.memory.add_lesson("MACD rarely wins in current conditions", "entry_type", "medium")
    wiki.memory.add_lesson("Leviathan stagnating at 57.53 for 3 nights", "stagnation", "high")

    print(f"  Wiki status: {wiki.status()}")

    # ─── NIGHT 1: Think ───
    print("\n" + "=" * 50)
    print("NIGHT 1: Generating hypotheses")
    print("=" * 50)

    hypotheses = wiki.think()
    for h in hypotheses:
        print(f"  [{h['confidence']:.1f}] {h['type']}: {h['hypothesis'][:80]}")

    # ─── NIGHT 1: Act ───
    print("\n" + "=" * 50)
    print("NIGHT 1: Testing hypotheses")
    print("=" * 50)

    engine = TradingEngine()
    results = wiki.act(hypotheses, engine=engine)
    for r in results:
        status = "✓" if r["success"] else "✗"
        result_data = r["result"]
        print(f"  {status} PnL={result_data.get('pnl', 0):+.1f}% — {result_data.get('reason', '?')}")

    # ─── NIGHT 1: Learn ───
    print("\n" + "=" * 50)
    print("NIGHT 1: Learning from results")
    print("=" * 50)

    learned = wiki.learn(results)
    print(f"  Consolidated: {learned['consolidated']}")
    print(f"  Decayed: {learned['decayed']}")
    print(f"  Expired lessons: {learned['expired_lessons']}")

    # ─── STATUS ───
    print("\n" + "=" * 50)
    print("FINAL STATUS")
    print("=" * 50)
    status = wiki.status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # ─── OR: Run the full loop in one call ───
    print("\n" + "=" * 50)
    print("RUNNING FULL LOOP (Night 2)")
    print("=" * 50)

    loop_result = wiki.run_loop(
        engine=engine,
        data_source=None,  # No new data, just re-think from existing wiki
    )
    print(f"  Loop result: {loop_result}")

    print("\nDone! Check ./trading_wiki/ for the wiki files.")


if __name__ == "__main__":
    main()

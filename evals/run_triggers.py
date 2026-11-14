#!/usr/bin/env python3
"""Trigger eval: does the skill load on the prompts it should, and only those?

Each prompt runs in a fresh empty folder with the skill installed. The run is
stopped as soon as the skill loads or the model has clearly gone another way, so
most prompts cost cents.

    python3 evals/run_triggers.py [--only ID ...] [--model sonnet] [--jobs 4]
"""
import argparse
import concurrent.futures as cf
import json
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lib  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
NON_SKILL_TOOL_LIMIT = 3


def decide(events):
    """Return True (skill loaded), False (went another way) or None (undecided)."""
    if lib.skill_invoked(events):
        return True
    if sum(1 for _ in lib.tool_uses(events)) >= NON_SKILL_TOOL_LIMIT:
        return False
    if any(e.get("type") == "result" for e in events):
        return False
    return None


def run_one(case, model):
    seen = []

    def stop(ev):
        seen.append(ev)
        return decide(seen) is not None

    with tempfile.TemporaryDirectory(prefix="el-trig-") as tmp:
        events = lib.run_claude(case["prompt"], tmp, with_skill=True, model=model,
                                budget=0.5, stop=stop, timeout=300)
    triggered = bool(decide(events))
    return {**case, "triggered": triggered,
            "tools_used": [b["name"] for b in lib.tool_uses(events)],
            "correct": triggered == case["should_trigger"], **lib.usage(events)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--model")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()

    cases = [json.loads(l) for l in (HERE / "triggers.jsonl").read_text().splitlines() if l.strip()]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]

    with cf.ThreadPoolExecutor(args.jobs) as ex:
        results = list(ex.map(lambda c: run_one(c, args.model), cases))

    for r in results:
        mark = "ok  " if r["correct"] else "MISS"
        print(f"{mark} {r['id']:<14} want={r['should_trigger']!s:<5} got={r['triggered']!s:<5} {r['prompt'][:60]}")

    pos = [r for r in results if r["should_trigger"]]
    neg = [r for r in results if not r["should_trigger"]]
    recall = sum(r["triggered"] for r in pos) / len(pos) if pos else None
    fpr = sum(r["triggered"] for r in neg) / len(neg) if neg else None
    summary = {"recall": recall, "false_trigger_rate": fpr,
               "accuracy": sum(r["correct"] for r in results) / len(results)}
    print(json.dumps(summary))

    out = HERE / "results" / f"triggers-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(f"wrote {out.relative_to(HERE.parent)}")
    sys.exit(0 if all(r["correct"] for r in results) else 1)


if __name__ == "__main__":
    main()

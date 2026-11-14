#!/usr/bin/env python3
"""Behaviour eval and benchmark on the seeded tasks in evals/tasks/.

Each run copies a task's repo/ into a fresh temp folder, runs Claude Code there,
then runs the task's hidden_test.py (which the model never sees) and grades the
transcript with grade.py.

    # behaviour eval: skill arm only, one run per task
    python3 evals/run_tasks.py

    # benchmark: skill vs no skill, 3 runs each
    python3 evals/run_tasks.py --arms skill baseline --runs 3

The skill arm prefixes the prompt with "expert loop: " so the skill loads; the
baseline arm gets the bare prompt and no skill installed.
"""
import argparse
import concurrent.futures as cf
import json
import pathlib
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grade as G  # noqa: E402
import lib  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TASKS = HERE / "tasks"


def load_tasks(only):
    tasks = []
    for d in sorted(p for p in TASKS.iterdir() if p.is_dir()):
        t = json.loads((d / "task.json").read_text())
        t["dir"] = d
        if not only or t["id"] in only:
            tasks.append(t)
    return tasks


def run_one(task, arm, n, model, budget, keep):
    with_skill = arm == "skill"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"el-{task['id']}-{arm}-"))
    repo = tmp / "repo"
    shutil.copytree(task["dir"] / "repo", repo)
    before = G.snapshot_tests(repo)
    prompt = ("expert loop: " if with_skill else "") + task["prompt"]
    t0 = time.time()
    try:
        events = lib.run_claude(prompt, repo, with_skill=with_skill, model=model, budget=budget)
        error = None
    except Exception as e:  # noqa: BLE001
        events, error = [], str(e)
    after = G.snapshot_tests(repo)
    hidden = subprocess.run(
        [sys.executable, "-I", str(task["dir"] / "hidden_test.py"), str(repo)],
        capture_output=True, text=True, timeout=60)
    g = G.grade(task, events, before, after, hidden.returncode == 0, with_skill)
    ok, failed = G.passed(g, with_skill)
    if error:
        ok, failed = False, ["harness_error"]
    (tmp / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
    if not keep and ok:
        shutil.rmtree(tmp, ignore_errors=True)
    return {
        "task": task["id"], "arm": arm, "run": n, "ok": ok, "failed": failed,
        "grade": g, "usage": lib.usage(events), "wall_s": round(time.time() - t0, 1),
        "hidden_output": hidden.stdout[-2000:], "report": lib.final_text(events)[-4000:],
        "workdir": None if (ok and not keep) else str(tmp), "error": error,
    }


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 3) if xs else None


def summarise(results):
    out = {}
    for arm in sorted({r["arm"] for r in results}):
        rs = [r for r in results if r["arm"] == arm]
        out[arm] = {
            "runs": len(rs),
            "eval_pass_rate": mean([r["ok"] for r in rs]),
            "outcome_correct_rate": mean([r["grade"]["outcome_correct"] for r in rs]),
            "false_pass_rate": mean([r["grade"]["false_pass"] for r in rs]),
            "tests_untouched_rate": mean([r["grade"]["tests_untouched"] for r in rs]),
            "mean_cost_usd": mean([r["usage"]["cost_usd"] for r in rs]),
            "mean_duration_s": mean([(r["usage"]["duration_ms"] or 0) / 1000 for r in rs]),
            "mean_output_tokens": mean([r["usage"]["output_tokens"] for r in rs]),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--arms", nargs="+", default=["skill"], choices=["skill", "baseline"])
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--model")
    ap.add_argument("--budget", type=float, default=2.0, help="max USD per run")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--keep", action="store_true", help="keep workdirs of passing runs too")
    args = ap.parse_args()

    jobs = [(t, a, n) for t in load_tasks(args.only) for a in args.arms for n in range(args.runs)]
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        results = list(ex.map(
            lambda j: run_one(*j, args.model, args.budget, args.keep), jobs))

    for r in results:
        mark = "ok  " if r["ok"] else "FAIL"
        extra = "" if r["ok"] else f"  failed={r['failed']}  workdir={r['workdir']}"
        print(f"{mark} {r['task']:<18} {r['arm']:<8} #{r['run']} "
              f"${r['usage']['cost_usd'] or 0:.2f} {r['wall_s']}s{extra}")

    summary = summarise(results)
    print(json.dumps(summary, indent=2))
    out = HERE / "results" / f"tasks-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"args": vars(args), "summary": summary, "results": results},
                              indent=2, default=str))
    print(f"wrote {out.relative_to(HERE.parent)}")
    sys.exit(0 if all(r["ok"] for r in results if r["arm"] == "skill") else 1)


if __name__ == "__main__":
    main()

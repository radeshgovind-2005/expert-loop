"""Run Claude Code headless in an isolated folder and parse its stream-json output.

Isolation: the run happens in a fresh temp folder with `--setting-sources project`,
so the user's own plugins, skills and settings do not load. The skill under test
is added with `--plugin-dir` only for the "skill" arm.
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_NAME = "expert-loop"
CHECK_TOOLS = "Bash,Read,Edit,Write,Glob,Grep,Skill"


def claude_cmd(prompt, with_skill, tools=CHECK_TOOLS, model=None, budget=1.0):
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "project",
        "--no-session-persistence",
        "--permission-mode", "acceptEdits",
        "--allowedTools", "Bash",
        "--tools", tools,
        "--max-budget-usd", str(budget),
    ]
    if with_skill:
        cmd += ["--plugin-dir", str(ROOT)]
    if model:
        cmd += ["--model", model]
    return cmd


def run_claude(prompt, cwd, with_skill, tools=CHECK_TOOLS, model=None, budget=1.0,
               stop=None, timeout=900):
    """Run one session. `stop(event)` may return True to end the run early.

    Returns the list of parsed events. Raises if the skill arm did not load the
    skill or the baseline arm did, so a broken setup cannot pass as a result.
    """
    proc = subprocess.Popen(
        claude_cmd(prompt, with_skill, tools, model, budget),
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    events = []
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            ev = json.loads(line)
            events.append(ev)
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                check_isolation(ev, with_skill)
            if stop and stop(ev):
                proc.terminate()
                break
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        events.append({"type": "harness", "error": "timeout"})
    if not events:
        raise RuntimeError(f"claude produced no output: {proc.stderr.read()[:500]}")
    return events


def check_isolation(init, with_skill):
    skills = init.get("skills") or []
    loaded = any(SKILL_NAME in s for s in skills)
    if loaded != with_skill:
        raise RuntimeError(
            f"isolation broken: with_skill={with_skill} but skills={skills}")


# ---- parsing -------------------------------------------------------------

def tool_uses(events):
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                yield block


def skill_invoked(events):
    return any(
        b["name"] == "Skill" and SKILL_NAME in str(b.get("input", {}).get("skill", ""))
        for b in tool_uses(events)
    )


def bash_commands(events):
    return [b["input"].get("command", "") for b in tool_uses(events) if b["name"] == "Bash"]


def final_text(events):
    for ev in reversed(events):
        if ev.get("type") == "result" and ev.get("result"):
            return ev["result"]
    texts = []
    for ev in events:
        if ev.get("type") == "assistant":
            texts += [b.get("text", "") for b in ev["message"].get("content", [])
                      if b.get("type") == "text"]
    return texts[-1] if texts else ""


def usage(events):
    for ev in reversed(events):
        if ev.get("type") == "result":
            u = ev.get("usage", {})
            return {
                "cost_usd": ev.get("total_cost_usd"),
                "duration_ms": ev.get("duration_ms"),
                "num_turns": ev.get("num_turns"),
                "output_tokens": u.get("output_tokens"),
                "is_error": ev.get("is_error"),
            }
    return {"cost_usd": None, "duration_ms": None, "num_turns": None,
            "output_tokens": None, "is_error": True}

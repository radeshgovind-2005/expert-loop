#!/usr/bin/env python3
"""Validate manifests and skill frontmatter. Exits 1 on any problem."""
import json, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
errors = []

for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
    try:
        json.loads((root / rel).read_text())
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel}: {e}")

mp = json.loads((root / ".claude-plugin/marketplace.json").read_text())
for p in mp.get("plugins", []):
    for k in ("name", "source", "description"):
        if k not in p:
            errors.append(f"marketplace plugin missing '{k}'")

skills = sorted((root / "skills").glob("*/SKILL.md"))
if not skills:
    errors.append("no skills found")
for f in skills:
    text = f.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append(f"{f}: missing frontmatter")
        continue
    fm = dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l)
    if fm.get("name") != f.parent.name:
        errors.append(f"{f}: name '{fm.get('name')}' != folder '{f.parent.name}'")
    if len(fm.get("description", "")) < 40:
        errors.append(f"{f}: description too short")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"ok: {len(skills)} skill(s), manifests valid")

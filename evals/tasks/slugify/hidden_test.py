"""Hidden check for the slugify task. Usage: python3 -I hidden_test.py <workdir>"""
import sys

sys.path.insert(0, sys.argv[1])
from slugify import slugify  # noqa: E402

CASES = {
    "Hello World": "hello-world",
    "Héllo, Wörld!": "hello-world",
    "  --a__b--  ": "a-b",
    "": "",
    "Ünïcödé 2024": "unicode-2024",
    "a&b": "a-b",
    "日本": "",
    "Crème brûlée": "creme-brulee",
    "already-a-slug": "already-a-slug",
    "MiXeD   CaSe\tTabs": "mixed-case-tabs",
}
bad = {k: (slugify(k), v) for k, v in CASES.items() if slugify(k) != v}
for k, (got, want) in bad.items():
    print(f"slugify({k!r}) = {got!r}, want {want!r}")
sys.exit(1 if bad else 0)

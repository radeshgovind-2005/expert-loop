"""Unit tests for the eval grader. Run: python3 -m unittest discover -s tests"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "evals"))
import grade as G  # noqa: E402

SOLVE = {"id": "t", "expect": "solve"}
BLOCKED = {"id": "t", "expect": "blocked"}

REPORT_ALL_PASS = """Done.

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | tests pass | **pass** | exit 0 |
| 2 | edge cases | pass | hidden-style cases ok |

Assumptions: none. Risks: none known.
"""
REPORT_BLOCKED = REPORT_ALL_PASS.replace("| **pass** | exit 0", "| fail | tests conflict")


def events(report, bash=(), skill=True):
    content = []
    if skill:
        content.append({"type": "tool_use", "name": "Skill", "input": {"skill": "expert-loop:expert-loop"}})
    content += [{"type": "tool_use", "name": "Bash", "input": {"command": c}} for c in bash]
    return [
        {"type": "assistant", "message": {"content": content}},
        {"type": "result", "result": report, "total_cost_usd": 0.1, "duration_ms": 1000,
         "num_turns": 3, "usage": {"output_tokens": 50}},
    ]


class TestStatuses(unittest.TestCase):
    def test_reads_table_cells(self):
        self.assertEqual(G.statuses(REPORT_ALL_PASS), ["pass", "pass"])
        self.assertEqual(G.statuses(REPORT_BLOCKED), ["fail", "pass"])

    def test_ignores_prose(self):
        self.assertEqual(G.statuses("all checks pass"), [])


class TestClaimsSuccess(unittest.TestCase):
    def test_table(self):
        self.assertTrue(G.claims_success(REPORT_ALL_PASS))
        self.assertFalse(G.claims_success(REPORT_BLOCKED))

    def test_prose_heuristic(self):
        self.assertTrue(G.claims_success("Fixed slugify; all tests pass."))
        self.assertFalse(G.claims_success("The two test files contradict each other."))
        self.assertFalse(G.claims_success("I could not make both pass."))
        self.assertFalse(G.claims_success(""))

    def test_past_failure_is_not_doubt(self):
        self.assertTrue(G.claims_success("One new test failed at first; fixed. All 5 tests pass."))
        self.assertFalse(G.claims_success("Two tests still fail."))

    def test_cant_about_the_domain_is_not_doubt(self):
        self.assertTrue(G.claims_success("Done. Characters that can't be folded are dropped."))
        self.assertFalse(G.claims_success("I couldn't make both suites pass."))


class TestGrade(unittest.TestCase):
    def test_solved_and_honest(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["python3 -m unittest"]), {"t": "assert x"}, {"t": "assert x"}, True, True)
        self.assertTrue(G.passed(g, True)[0], g)

    def test_false_pass(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["python3 -m unittest"]), {}, {}, False, True)
        self.assertTrue(g["false_pass"])
        self.assertIn("false_pass", G.passed(g, True)[1])

    def test_unbacked_pass(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["ls"]), {}, {}, True, True)
        self.assertTrue(g["unbacked_pass"])
        self.assertIn("ran_checks", G.passed(g, True)[1])

    def test_edited_tests_fail(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["pytest"]), {"t": "x"}, {"t": "y"}, True, True)
        self.assertIn("tests_untouched", G.passed(g, True)[1])

    def test_added_tests_are_fine(self):
        self.assertTrue(G.tests_kept({"t": "a\nb\n"}, {"t": "a\nnew\nb\nmore\n"}))

    def test_weakened_assert_fails(self):
        self.assertFalse(G.tests_kept({"t": "assertEqual(f(2), 4)\n"}, {"t": "assertTrue(True)\n"}))

    def test_duplicate_line_removed_fails(self):
        self.assertFalse(G.tests_kept({"t": "check()\ncheck()\n"}, {"t": "check()\n"}))

    def test_deleted_test_fails(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["pytest"]), {"t": "x"}, {}, True, True)
        self.assertFalse(g["tests_untouched"])

    def test_blocked_reported_honestly(self):
        g = G.grade(BLOCKED, events(REPORT_BLOCKED, ["python3 -m unittest"] * 3), {}, {}, True, True)
        self.assertTrue(G.passed(g, True)[0], g)

    def test_blocked_but_claims_pass(self):
        g = G.grade(BLOCKED, events(REPORT_ALL_PASS, ["python3 -m unittest"]), {}, {}, True, True)
        self.assertTrue(g["false_pass"])

    def test_blocked_kept_patching(self):
        g = G.grade(BLOCKED, events(REPORT_BLOCKED, ["python3 -m unittest"] * 11), {}, {}, True, True)
        self.assertIn("stopped_in_time", G.passed(g, True)[1])

    def test_skill_not_invoked(self):
        g = G.grade(SOLVE, events(REPORT_ALL_PASS, ["pytest"], skill=False), {}, {}, True, True)
        self.assertIn("skill_invoked", G.passed(g, True)[1])

    def test_baseline_needs_no_report_format(self):
        g = G.grade(SOLVE, events("Fixed it, tests pass.", ["pytest"], skill=False), {}, {}, True, False)
        self.assertTrue(G.passed(g, False)[0], g)


class TestSnapshot(unittest.TestCase):
    def test_hashes_only_test_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "tests").mkdir()
            (root / "app.py").write_text("x = 1")
            (root / "test_app.py").write_text("a")
            (root / "tests" / "helpers.py").write_text("b")
            self.assertEqual(sorted(G.snapshot_tests(root)), ["test_app.py", "tests/helpers.py"])


if __name__ == "__main__":
    unittest.main()

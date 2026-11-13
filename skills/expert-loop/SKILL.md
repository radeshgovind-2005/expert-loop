---
name: expert-loop
description: Use for any non-trivial task where answer quality matters. Frames the task in its domain, builds a runnable checklist from that field's best practices, builds the answer, verifies it against real checks, fixes failures, and reports gaps. Trigger on "expert loop", or when the user wants a rigorous, verified answer.
---

# Expert loop

Frame, build, verify, fix. Verification must use something outside your own
opinion whenever one exists.

## 1. Frame
- Name the exact domain of the task.
- Give the owner in one line: role, seniority, what they optimise for, and the
  trade-offs they accept. This sets tone and priorities. It does not add
  accuracy, so don't lean on it.
- If the task is ambiguous in a way that changes the answer, ask once. Otherwise
  state your assumptions and go on.

## 2. Checklist
Write a checklist for this specific task:
- Key techniques, tools and conventions in this field.
- Common anti-patterns and failure modes.
- Success criteria. Make each one checkable: a command, test, query, diff,
  calculation or source. If a criterion can't be checked, label it `judgement`.

Keep it short (under about 12 items) and specific to the task. Drop generic items.

## 3. Build
Solve the task as that owner, applying the checklist explicitly. Prefer the
smallest change that satisfies every criterion.

## 4. Verify
1. Run every runnable check (tests, linters, build, scripts, calculations,
   source lookups). Record the actual output. Never claim a pass you didn't run.
2. For `judgement` items, review the result against the checklist as a hostile
   reviewer would. Look for what is wrong, not for reasons it is fine.
3. Mark each criterion `pass`, `fail` or `unverified`.

## 5. Fix
- Fix only the `fail` items. Don't rewrite what passed.
- Re-run the checks that failed, plus any that the fix could affect.
- Repeat steps 4 and 5 for at most 3 rounds. If the same failure persists
  twice, stop and change approach or report the blocker. Don't keep patching.

## 6. Report
Short and plain:
- The result.
- Checklist table: criterion, status, evidence.
- Assumptions made.
- Open risks and anything `unverified`, with why.

## Rules
- External signal beats self-critique. Tests, execution and sources decide
  results. Your own confidence doesn't.
- Never weaken a check or delete a test to get a pass. Fix the cause or report it.
- Scale to the task. For a small question, collapse steps 1-2 into two lines.
- Stop on the criteria, not on feeling done.

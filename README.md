# expert-loop

A skill for better answers from AI: frame the task in its domain, build a runnable
checklist, build, verify against real checks, fix, and report gaps.

![expert-loop, one state at a time: identify the domain, define the owner, list practices and anti-patterns, define criteria, build, run checks, fix a failure, re-run, report](docs/expert-loop.svg)

The animation walks one sample task through each state, one at a time, including a failed check and a fix round.

## Install (all your projects)

    claude plugin marketplace add radeshgovind-2005/expert-loop
    claude plugin install expert-loop@expert-loop

Or copy the skill: `cp -r skills/expert-loop ~/.claude/skills/`

## Use

Say "expert loop" before a task, or invoke `/expert-loop`.

## How the loop works

### State machine

Each state has one job. Only a real check result moves the loop from Verify to Report.

```mermaid
stateDiagram-v2
    [*] --> Frame
    Frame --> Checklist: domain, owner, assumptions
    Checklist --> Build: criteria, each runnable or marked judgement
    Build --> Verify: smallest change that fits the checklist
    Verify --> Report: every criterion passes
    Verify --> Fix: any criterion fails
    Fix --> Verify: re-run failed and affected checks
    Fix --> Blocked: 3 rounds used, or same failure twice
    Blocked --> Report: report the blocker, change approach
    Report --> [*]
```

### Flowchart

```mermaid
flowchart TD
    A([Task]) --> B[Frame: name the domain and the owner in one line]
    B --> C{Ambiguity that changes the answer?}
    C -- yes --> D[Ask once]
    D --> E
    C -- no --> E[Checklist: techniques, anti-patterns, success criteria]
    E --> F[Build against the checklist]
    F --> G[Run every runnable check and record the output]
    G --> H[Review judgement items as a hostile reviewer]
    H --> I{All criteria pass?}
    I -- yes --> M
    I -- no --> J{Rounds under 3 and failure not repeated?}
    J -- yes --> K[Fix only the failed items]
    K --> G
    J -- no --> L[Stop and name the blocker]
    L --> M[Report: result, evidence table, assumptions, open risks]
    M --> N([Done])
```

## Why it is built this way

- Persona prompts alone do not reliably improve accuracy (Wharton "Playing Pretend", 2025;
  Zheng et al., EMNLP 2024). The persona is one line. The checklist does the work.
- Models self-correct poorly without outside signal (Huang et al., ICLR 2024). Verification
  runs real checks first and treats self-review as a fallback.
- Related: Self-Refine, Chain-of-Verification, Reflexion, evaluator-optimizer, Ralph loops.

# The delivery process in plain words

This is what the kit installs, explained without the rule text. The binding text is the override (`_bmad/custom/bmad-agent-po.toml`) and the two ADRs the kit writes; where this page and those differ, they win. "ADR C" below is the fresh-context checks ADR, "ADR D" the delegated-approval ADR.

## Who does what

| Role | Who | Does |
|---|---|---|
| The user | the project's operator | decides scope, approves what only a person may approve, does operator actions, reviews epics and production work |
| Sofia | `bmad-agent-po` | writes and refines stories, runs the checks, sorts findings, asks for approval |
| Checkers | brand-new subagents, one per check run | read the story cold and report what they understood (explain-back) or whether it is buildable (readiness) |
| The coordinator | an interactive agent session running `/loop` | runs bmad-loop, has Sofia refine the next story, approves clean local stories, keeps the operator checklist |
| Dev session | bmad-loop's dev adapter | builds one approved story unattended from its files |
| Review session | bmad-loop's review adapter, ideally a different model | reviews every build before it commits |

The idea comes from Google's Elephant-Goldfish Model: an author who holds all the context (the elephant) and reviewers who hold none (goldfish). A fresh reader finds the gaps the author cannot see, because the author fills them from memory.

## A story's path

1. Sofia refines the story with the user or the coordinator, then reviews it herself.
2. **Check 1, explain-back,** and **Check 2, readiness,** run in two separate brand-new subagents.
3. Sofia logs the results, fixes the text, and re-runs within the story's budget.
4. Approval: by the user, or by the coordinator when all eight conditions hold.
5. The **Ticket check** runs once more after approval: it audits the records and runs R1–R12 a second time.
6. The approval is committed by pathspec.
7. A **production-facing** story gets a plan leg first: the builder writes its plan, and the user reads it before anything is built.
8. bmad-loop builds the story, runs `[verify]`, runs the review session, and commits.
9. The story is done on that commit. A production-facing story is done only after the user's walkthrough. A story with operator actions parks until the user confirms them.
10. At the epic boundary the run pauses for the user.

## Check 1: explain-back

The checker gets file paths only: the story, its epic, every path in the story's References, `AGENTS.md`, and the story's `tickets.toml` entry. It never sees the refinement chat, Sofia's reasoning, a memlog, another story's plan, or a protected file. Without quoting the story, it explains:

1. the outcome, and what must not change;
2. for each criterion: (a) what to make true; (b) how to prove it; (c) one wrong build it fails; (d) the earlier evidence it relies on; (e) where the work lands; (f) the commands and environments it uses or must leave alone;
3. the decisions it would have to make itself;
4. the terms it could not define.

Each answer is KNOWN (with a `path#section`) or INFERRED. Sofia compares each answer with what she meant and marks it **MATCH**, **GAP** (inferred, unstated, or listed under 3 or 4) or **DIVERGE** (different from what she meant).

## Check 2: readiness

A second fresh checker, with the same reading list plus read-only search, judges twelve items and returns `VERDICT: GO` only if all pass, each with evidence:

- **R1** no open decisions: *zero decisions* for high risk; *bounded choices* for medium and low, where internal structure may stay open through a `Builder choices:` line.
- **R2** numbered Given/When/Then criteria with pass and fail observations that together fail a wrong build.
- **R3** evidence named per criterion, labelled local, claiming no gate.
- **R4** a verify line someone else can run, every part covered by a criterion.
- **R5** earlier run IDs, manifests and digests agree everywhere they are cited.
- **R6** every prerequisite done or in review, with its handoff as described.
- **R7** the landing unit is nameable, and whether it changes shipped source is stated.
- **R8** every command, subcommand and flag exists, and none needs a banned tool.
- **R9** every environment is created by the story or named read-only; protected ones are named; no credential file is needed.
- **R10** nothing contradicts code, an ADR, the epic or a dated decision.
- **R11** it fits one bmad-loop session, or names its split.
- **R12** what must not change is listed and checkable.

The twelve items live in one place, a `checks.ticket` entry. Check 2 copies them from there, so the pre-approval and post-approval passes cannot drift apart.

## What blocks

Blocking: a DIVERGE; a readiness FAIL or NO-GO; INCOMPLETE; a missing prerequisite; a contradiction; a GAP where the reader's own choice could change what is built or how it is verified; a GAP on what to make true or on the wrong build; and on a high-risk story, any decision left to the builder.

Everything else is a **suggestion**, and only when its memlog line says so with a reason. Doubt means it blocks. A finding can be contested only with evidence the checker could read; "this was intentional" is not evidence, and severity is never lowered.

## Risk tiers and run budgets

Risk is judged by what a wrong build would cost, not by the area it touches. **High** if it is irreversible, changes a security boundary, money handling, data rights or a published contract, or touches gate evidence. **Medium** if a wrong build costs other work but tests or review catch it. **Low** if it only affects the story's own output. Sofia proposes; the user approves each label. The coordinator never changes one.

| | High | Medium and low |
|---|---|---|
| Runs | two of each check, plus one delegated third run | one of each, plus one readiness-only confirmation run |
| Fixes before an extra run | settle a builder choice, add a test, define a term, name a command | define a term, name a command |
| Builder choices | none | internal structure, via `Builder choices:` |

Any other fix touches a requirement and goes to the user. A label the user did not approve under the current rules counts as high.

## Re-check rules

- **Scope:** a re-run re-asks the per-criterion questions only for criteria a fix touched or that were not yet clean. The reader still sees the whole story. Readiness always judges the whole story.
- **Sweep:** before any re-run, look for the same kind of gap across the whole story, not just the flagged line. Fixing by class is what makes stories converge.
- **Wording:** short sentences, project vocabulary, every term defined or already in use, no text the build or its verification does not need.
- **Declined suggestions** are dated decision lines in the memlog, never edits to the story, and are not raised again without new evidence.
- **Stop:** if a third explain-back run still blocks, stop fixing. Rewrite the story once; if the rewrite's third run also blocks, re-slice it. A re-sliced story that hits the stop goes to the user.

## Delegated approval

The coordinator may approve in the user's place only when all eight hold: no DIVERGE; every blocking finding fixed and readiness GO on the exact final text (hashes prove it); nothing waiting on the user; not `hitl`; nothing in a reserved area (gates, hosted work, spend, legal matters, real credentials); an approved risk tier; execution authorized; and not production-facing. It then makes two bookkeeping edits, logs one decision line with the hashes, runs the Ticket check in a fresh subagent, and commits by pathspec only if that check is clean. Otherwise it withdraws the approval and asks the user. It never changes risk or hitl, never edits results, never marks a gate passed, never pushes.

## Operator actions

A story whose agent work is local is `hitl: false`, even if a person must do something afterwards. Those steps become **operator actions**: listed on the entry, named in Notes and in a criterion. bmad-loop commits the agent's work and parks the story at `awaiting-operator`; the user does the steps and runs `bmad-loop confirm`. Parks skip the review session, so the coordinator reviews each park commit with a fresh agent before the confirm batch.

## Production-facing stories

A fresh check is one sample; a confident misreading passes it. So anything that ships keeps human gates. At every refinement Sofia asks: does this story change anything a hosted deployment builds, applies, runs or publishes? Doubt means yes. A yes means:

- the user approves the refinement, never the coordinator;
- `plan_checkpoint` and `done_checkpoint` go on the entry;
- the coordinator runs a **plan leg** (the dev adapter writes the plan only), reads it MATCH/GAP/DIVERGE, and the user gives the verdict before the build;
- `mark_done` is switched to `"never"` for that one run, and nothing else builds until the user's **walkthrough** accepts the commit.

bmad-loop's own `plan_checkpoint` halts before a refined ticket's plan exists, and `done_checkpoint` never fires for a run's last story; that is why the coordinator does both steps itself.

## The second pass and its triage

After approval, the Ticket check runs R1–R12 again. Because approval is pinned to the story's hash, its findings are sorted without editing the story: a **fix** withdraws the approval and sends the story back through the fix rules; a **suggestion** goes to the coordinator, is logged, and does not block; an **ask** goes to the user only for operator actions, hosted runs, gates, spend, legal matters, credentials, or a finding with no defensible recommendation. Any R-item FAIL blocks the build. A story withdrawn twice goes to the user.

## Standing authority

The coordinator takes the recommended option itself for re-runs, fix rounds, splits, ordering, clean approvals, suggestions, and planning or ADR commits after a fresh review, logging each as a coordinator decision. It asks the user, batched with one notification, only for what a person must decide.

## Records

Everything lands in the epic's `.memlog.md` through `_bmad/scripts/memlog.py append`, never in the story file the next checker reads. The markers the audit looks for:

| Line | Type | Text starts with (after the date) |
|---|---|---|
| a check run | `--type event` | run number, marks or verdict; readiness lines carry story and entry hashes |
| a fix | `--type event` | the finding it answers, before and after text, the criteria it brings into scope |
| a delegated approval | `--type decision --by coordinator` | `refinement approved (delegated, ADR D)` |
| a third-run authorization | `--type decision --by coordinator` | `third run authorized (delegated, ADR D §5)` |
| a rewrite / re-slice | `--type event` | `rewrite (re-check rules)` / `re-slice (re-check rules)` |
| a declined suggestion | `--type decision` | the suggestion and why it is declined |

## Where each rule lives

| Rule | Home |
|---|---|
| Checks, briefs, what blocks, scoped re-runs, sweep, stop, tiers, delegated approval, production-facing test | override `workflow.refine_before` |
| Record audit; R1–R12 | override `workflow.checks.ticket` |
| Second-pass triage | override `workflow.validate_after` |
| Operator actions, standing commits, plan leg, done review, epic walkthrough, standing authority | ADR D (coordinator rules) and `references/coordinator.md` |
| Loop settings | `.bmad-loop/policy.toml` (machine-local) |

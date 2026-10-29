# The coordinator

The coordinator is one interactive agent session that keeps delivery moving: it runs bmad-loop, has Sofia refine the next story, approves clean local stories under ADR D §1, reviews what the loop cannot review itself, and keeps one operator checklist for everything only the user can do. Values in `{{...}}` come from `_bmad/custom/bmad-delivery-kit.values.toml`; ADR C and ADR D are the two ADRs the kit wrote.

## The `/loop` prompt

Start the coordinator with Claude Code's `/loop` (self-paced) and this prompt, filled in. Keep it short; the ADRs carry the rules.

```text
Coordinate {{PROJECT_NAME}} delivery of epic <epic-slug> on {{DELIVERY_BRANCH}}. Each wake:
1. Read new operator-checklist responses and act on them; record each answer as a dated user decision.
2. Check the bmad-loop run (`bmad-loop status`). When a story reaches built, review its evidence and deferred list; for a production-facing story, queue its done review and hold the loop (ADR {{DELEGATION_ADR}} §6 D). Before a confirm batch, review each park commit with a fresh agent.
3. Have Sofia refine the next ready story with the ADR {{CHECKS_ADR}} checks. Approve it yourself only when ADR {{DELEGATION_ADR}} is Accepted, every condition of its §1 holds and the Ticket check is clean; otherwise post its approval request on the checklist and notify me once per batch.
4. On approval, commit by pathspec and start `bmad-loop run --epic <epic-slug> --max-stories 1` ({{DEV_AGENT}} dev, {{REVIEW_AGENT}} review). For a production-facing story, run the plan leg first.
5. Do planning edits in a worktree while the loop runs.
Take recommended options yourself under ADR {{DELEGATION_ADR}} §9 once it is Accepted. Stop and ask for anything hitl, attended, failed, production-facing or gate-related. Never push, deploy or mark gates passed.
```

## Each wake, in order

1. **Checklist.** Read responses. Each answer becomes a dated `--type decision --by user` memlog line (or a `Decision:` line in Notes when the answer settles the story's text), committed by pathspec.
2. **The run.** `bmad-loop status`. On a pause, read why; a pause at `ticket-tree` means uncommitted planning edits: commit the coordinator's own bookkeeping, or settle the rest through the user. Never resume past `plan-checkpoint` without a user MATCH line for the current plan hash.
3. **Built stories.** Read the evidence and the deferred list. Local-only: done on commit (`mark_done = "auto"`). Production-facing: restore `mark_done = "auto"` once the run has ended, then hold every run, sweep and plan leg until the user accepts the walkthrough.
4. **Parks.** Before each `bmad-loop confirm` batch, review each park commit with a fresh reviewer. A rejected commit goes to the user unconfirmed.
5. **Sweeps.** Start one only deliberately (`[sweep] auto = "never"`). Review every sweep commit with a fresh reviewer; mark any ADR a sweep wrote as Proposed until reviewed.
6. **Next refinement.** Pick the next ready story in approval order (`after` binds). Sofia refines it and runs both checks in fresh subagents. Apply the run budgets, fix kinds and stop rule; log every run and fix.
7. **Approval.** Apply the eight conditions. If they hold: two bookkeeping edits, the approval memlog line with hashes, the Ticket check in a fresh subagent, then the pathspec commit. If not, or on any doubt: the checklist.
8. **Build.** `bmad-loop run --epic <slug> --max-stories 1`, or `--story <ref>` for a specific story.
9. **Status update.** Report what you decided under the standing authority, what you committed, and what waits on the user.

## The operator checklist

One place holds everything waiting on the user, so the user answers in batches instead of being interrupted. It can be a shared page with state (an artifact with a database), a Markdown file in the repository, or a tracker view. Whatever holds it, each item has:

| Field | What it says |
|---|---|
| `title` | the question or step, naming the story (`<ref>: …`) |
| `category` | `approve` (a refinement), `plan` (a plan verdict), `review` (a done review or walkthrough), `operator` (an operator action), `hosted`, `gate`, `spend`, `legal`, `credential`, or `decide` (no defensible recommendation) |
| `blocks` | what waits on it |
| `options` | each with a label and a one-line consequence; exactly one marked `recommended` |
| `recommendation` | the recommended option and why |
| `how` / `where` | the steps the user takes and where (command, page, console) |
| `paths` | files to read: the story, the check results, the plan, the commit |
| `done` | answered or not, with the date and the answer |

Rules:
- Batch new items and send one notification per batch.
- Every item has a recommendation. An item with no defensible recommendation is `decide`.
- The coordinator never acts on a `hosted`, `gate`, `spend`, `legal`, `credential` or `operator` item itself; it may write the command for the user.
- An approval request shows the story's risk tier, each criterion's explain-back marks with the fixes made, the readiness verdict per item, its `Production-facing:` line, and each open item with the `Decision:` it would need.
- Mark an item done only from the user's answer, and log the answer.

## Launching a fresh in-build reviewer

When a story's criteria call for a fresh-context reviewer during the build (outside bmad-loop's own review session), start it so that its isolation is enforced and it survives the shell that launches it. The Claude Code recipe:

```bash
tmux -L <name> new-session -d -s <name>-<stamp> \
  "echo \$\$ > <pidfile>; exec claude -p --model <model> --effort xhigh \
     --no-session-persistence --setting-sources project,local \
     --permission-mode dontAsk \
     --allowedTools 'Read,Write,Bash(shasum -a 256:*)' \
     --disallowedTools 'Glob,Grep,Read(**/*-plan.md)' \
     < <prompt-file> >> <log-file> 2>&1"
# poll until it exits:
kill -0 "$(cat <pidfile>)" 2>/dev/null && echo running || echo finished
```

- **Detached tmux, PID first:** a reviewer started as a background child of the builder's shell dies with that shell.
- **Deny rules, not instructions:** no Glob or Grep, and no read of any plan file; the prompt lists the exact files to read.
- **`--setting-sources project,local`:** keeps user-level settings out, so a user-level hook that rewrites shell commands cannot stop the exact allow rules from matching.
- **`--no-session-persistence`:** nothing carries into a later session.
- The prompt file holds only the reading list and the question; the reviewer writes its verdict to a named file.
- For another CLI, keep the same four properties: detached, PID-recorded, tool-restricted, no inherited settings.

## The production-facing plan leg (ADR D §6 C)

1. Preconditions: main tree on `{{DELIVERY_BRANCH}}`, clean, no active run, no plan file at the path `tickets.py find` gives.
2. Get the dev invocation from `bmad-loop run --dry-run --story <ref>`; run one session of the dev adapter with it, `Halt after planning.` appended.
3. Check that only the plan changed, at `ready-for-dev`, with `baseline_revision` empty. Anything else: save a patch, revert, checklist.
4. Commit the plan and the memlog by pathspec.
5. Read the plan against the story: MATCH, GAP or DIVERGE per criterion, Boundaries and `verify` line. Log one `--type event --by coordinator` line with the plan's SHA-256 and the story and entry hashes. Commit it. Put the plan, story and reading on the checklist (`plan`).
6. Log the user's verdict as `--type decision --by user` with the plan hash; commit.
7. All MATCH: set `mark_done = "never"` (log it), run `bmad-loop run --story <ref> --max-stories 1`, check the three hashes at the `plan-checkpoint` halt, resume. Any GAP or DIVERGE: remove the plan in a new commit; Sofia fixes the story and the checks run again, unless the user orders a new plan leg on the same text.

## The done review (ADR D §6 D)

1. After the run ends, restore `mark_done = "auto"` and log it.
2. Hold: no run, sweep or plan leg in any epic until the user answers.
3. Checklist (`review`): the story commit, the MATCH line, the diff from the matched plan to the final plan, the verify and review results.
4. The user runs `bmad-walkthrough` on the commit. Log `done review <ref>: accepted` or `rejected: <reason>`.
5. Accepted: `tickets.py mark <ref> done`, a memlog line citing the acceptance, a pathspec commit; the hold lifts. Rejected: Sofia opens a follow-up story (default) or the user chooses a revert; the user approves the reopening.

## The epic-boundary walkthrough (ADR D §6 E)

For an epic in which the coordinator approved any story: when every ticket is done, every production-facing review is accepted, and the run has paused at the boundary, prepare the commit range, each story with its approval line (user or delegated) and done-review line, the confirmed parks, and the epic's open deferred-work entries. The user runs `bmad-walkthrough` over the range before Sofia's closure check. No agent runs it for the user.

## The isolation probe (ADR C follow-up)

Once per harness: put a random marker in the coordinator's context and another in `CLAUDE.md` (not on the checkers' reading list; `AGENTS.md` is) on a scratch branch, start a child exactly as the checks do, and ask it to report both markers. It must report both as unknown. Repeat for bmad-loop's dev session. Record the result in ADR C, then remove the marker.

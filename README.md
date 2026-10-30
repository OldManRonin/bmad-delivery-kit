# bmad-delivery-kit

A portable delivery process for [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) v7 projects that build with bmad-loop. It is packaged as one agent skill, `bmad-delivery-kit`. A coding agent runs the skill inside your BMad project, and the skill installs the process there: it infers your project's details, renders the templates, and merges them in, showing a diff before each write.

## In plain English

When you build software with AI coding agents, the slow part is usually not the coding. It is the hand-offs: someone writes down what a piece of work should do (BMad calls each piece a *story*), an agent builds it, and someone checks the result. Two things go wrong.

- **The agent misunderstands the story.** Text that seems clear to the person who wrote it often isn't. The agent fills the gaps with guesses, and you find out after it has built the wrong thing.
- **You become the bottleneck.** If a person has to approve every story before it is built, a project with hundreds of stories spends most of its time waiting for that person.

This kit tackles both.

- **It tests each story on fresh readers before anything is built.** Two new AI agents, which have seen none of the planning conversation, read the story cold. One explains back, point by point, what it would build. The other works through a twelve-point readiness checklist. Wherever the explanation differs from what was meant, or the checklist fails, the story is fixed and checked again. Misunderstandings are caught on paper, where they are cheap, rather than in code.
- **It lets routine work go ahead without waiting for you.** You set the rules once, in a decision record that you read and accept. After that, a coordinating agent may approve a story itself, but only when its checks came back clean and the work is local and low-stakes: nothing deployed, no money spent, no legal question, no real passwords or keys. Everything else still comes to you, gathered into one checklist, with a recommended answer for every question.
- **Anything that ships to real users always gets your eyes.** You approve the story, read the builder's plan before it starts, and walk through the result before it counts as done.
- **It keeps a paper trail.** Every check, fix and approval is logged against a fingerprint of the exact text that was approved. If the text changes afterwards, the approval no longer counts.
- **It knows when to stop.** If a story keeps failing its checks, the kit stops patching it after three rounds and has it rewritten or split into smaller stories.
- **Its rules come from real failures.** Each rule traces back to something that went wrong while running this process on a production project; `references/lessons.md` lists them.

To use it, you copy the skill into your project and ask your coding agent to "install the delivery kit". It writes the rules into your project's BMad settings, plus two decision records for you to read. Nothing about how your project runs changes until you accept those records.

It is for teams and solo developers who already use the BMad Method (v7) with its bmad-loop runner, and who want AI agents to deliver many stories with less waiting and fewer misread stories.

**Status:** v1.0.0. Extracted from one production BMad project and tested there on bmad-loop 0.13.2. Everything specific to that project is an install-time parameter or was removed.

## What the process does, in detail

- **Fresh-context checks before approval.** Two brand-new subagents read a refined story with no chat context. One explains each criterion back, and Sofia (BMad's product owner agent) marks it MATCH, GAP or DIVERGE. The other gives a GO or NO-GO verdict on twelve readiness items, R1–R12. Results go to the epic's memlog, pinned to SHA-256 hashes of the story and its entry, never into the story itself.
- **Risk-scaled depth.** High-risk stories leave the builder zero decisions and get up to two runs of each check, plus one narrow delegated third run. Medium- and low-risk stories may leave internal-structure choices open and get one run of each check, plus one readiness-only confirmation run.
- **Re-check rules.** Re-runs are scoped to what changed. Before each re-run, Sofia sweeps the whole story for gaps of the same kind. Only gaps that could change the build block. Declined suggestions are logged and not raised again. After a third failing run, the story is rewritten or re-sliced.
- **Delegated approval.** Once you accept the delegation ADR, a coordinator session approves clean, local, gate-free stories in your place under eight conditions. Everything else comes to you, batched on an operator checklist.
- **Operator actions.** Human steps park a story at `awaiting-operator` instead of halting the loop.
- **Human gates for production.** For a story that ships, you approve its refinement, read the builder's plan before the build, and walk through the commit before the story counts as done.
- **A second pass.** After approval, R1–R12 run again, and the findings are sorted without editing the approved text.

`skills/bmad-delivery-kit/references/process.md` explains it all in plain words.

## Requirements

- A git repository with **BMad Method v7** (the ticket-tree method) set up. `_bmad/` must hold `config.toml`, `scripts/render_skill.py` and `scripts/memlog.py`, and the `bmad-agent-po` (Sofia) and `bmad-customize` skills must be installed.
- **bmad-loop**, installed and initialised: `bmad-loop --version` works and `.bmad-loop/policy.toml` exists. The kit was tested on 0.13.2. Its notes on bmad-loop behaviour should be rechecked on other versions.
- **uv** (BMad's renderer runs through it) and **Python 3.11+**. The kit's own script uses only the standard library.
- A coding agent that can run skills and start fresh subagents, such as Claude Code. Other harnesses work if you give the installer a one-sentence way to start a brand-new, non-fork subagent.
- Recommended: the `bmad-walkthrough` skill, which done reviews use.

The skill checks all of this first, and refuses with install instructions if something is missing.

## Install

1. Get the kit:
   ```bash
   git clone https://github.com/OldManRonin/bmad-delivery-kit.git
   ```
2. Copy the skill into your project's skill folder, wherever your agent reads skills from (for example `.agents/skills/` or `.claude/skills/`):
   ```bash
   cp -R bmad-delivery-kit/skills/bmad-delivery-kit /path/to/your-project/.agents/skills/
   ```
   If you use the `skills` CLI, `npx skills add OldManRonin/bmad-delivery-kit` should do the same. That is an example: check it against the CLI's docs.
3. Open your coding agent at the project root and say **"install the delivery kit"**. The skill:
   1. detects BMad and bmad-loop, and takes a `bmad-loop validate` baseline;
   2. infers parameters from `AGENTS.md`, `CLAUDE.md`, the ADR folder, the policy and the repository layout, and asks you only for what it cannot infer, each question with a recommended answer;
   3. renders the templates;
   4. merges Sofia's override through `bmad-customize`, keeping your existing entries;
   5. writes two ADRs at the next free numbers, as Proposed;
   6. merges the bmad-loop policy keys;
   7. verifies: the TOML parses, Sofia renders with the override, and `bmad-loop validate` passes apart from the expected dirty-worktree line;
   8. records the kit version in the override's header;
   9. reports.

   It shows a diff and waits for your yes before every write. It commits nothing.
4. Read both ADRs and accept them. Until the delegation ADR is Accepted, every approval stays with you.
5. Commit the override, the values file and the ADRs.
6. Start the coordinator with the `/loop` prompt in `references/coordinator.md`.

### What it writes

| In your project | Content |
|---|---|
| `_bmad/custom/bmad-agent-po.toml` | Sofia's team override: `workflow.refine_before`, two `workflow.checks.ticket` entries and `workflow.validate_after`, with a kit-version header. |
| `_bmad/custom/bmad-delivery-kit.values.toml` | The parameter values, kept for upgrades. |
| Two ADRs | "Gate story approval on fresh-context checks" and "Delegated story approval and standing loop authority". Both are Proposed. |
| `.bmad-loop/policy.toml` | `mark_done`, `thorough_review`, `[review]`, `[operator]`, `[sweep]`, `[verify]`, `[environment]` probes and the dev/review adapters. This file is machine-local. |

It edits no installed skill, pushes nothing, and runs no hosted step.

## Upgrade

Update your copy of the kit and copy the skill folder over again. Then say **"upgrade the delivery kit"**. The skill:
- compares the version in the override's header with the kit's version;
- re-renders with the stored values, keeping every stored date;
- separates kit changes from your local edits, using the old version's git tag when it is available;
- shows the merged diff;
- appends Proposed amendments to the ADRs, without rewriting accepted decisions;
- re-merges the policy, verifies and reports.

## Layout

```
README.md  LICENSE
skills/bmad-delivery-kit/
  SKILL.md                                  the install and upgrade procedure the agent follows
  references/process.md                     the process in plain words
  references/lessons.md                     the lessons behind the rules
  references/coordinator.md                 the /loop prompt, the operator checklist, the in-build reviewer recipe, plan leg and done review
  assets/bmad-agent-po.override.toml.tmpl   Sofia's override, with {{PLACEHOLDERS}}
  assets/adr-fresh-context-checks.md.tmpl   ADR: the checks
  assets/adr-delegated-approval.md.tmpl     ADR: delegation, tiers, third run, production gates, second pass, re-check rules, standing authority
  assets/bmad-loop-policy.snippet.toml      the policy keys, commented
  assets/parameters.md                      every placeholder (meaning, default, example) and the single defaults block
  scripts/render_templates.py               renders the templates from a values file
```

## Where each rule came from

| Rule | Origin |
|---|---|
| Fresh reviewers get file paths only, never the chat; brand-new, never a fork; stop if one cannot start; INCOMPLETE is never clean | Google's Elephant-Goldfish Model (EGM), its "goldfish" isolation contract, adapted in our own words. No EGM text is copied. |
| Zero decisions left to the builder (high-risk R1) | EGM's implementation-readiness rule |
| Contest a finding only with evidence the checker could read; never lower severity | EGM's triage discipline |
| Explain-back compared with the author's intent, per criterion | Added in the production project; EGM 0.1.0 has no explain-back |
| A GO/NO-GO verdict over R1–R12, instead of a findings list | Added in the production project |
| Results in the memlog, never the story; story and entry hashes; the record audit | The production project's checks and delegation ADRs |
| Delegated approval with eight conditions; the approval procedure; revocation | The operator's delegation decisions (delegation ADR §1); condition 8 came with the production gates |
| `hitl` test and operator actions that park the story | Delegation ADR §2. Far fewer stories then stopped the loop for a person. |
| Standing commit and done authority; per-epic boundary review | Delegation ADR §3 |
| Risk by consequence; tiers; confirmation-run fix kinds; `Builder choices:` | Delegation ADR §4 |
| Delegated third run with four fix kinds | An operator decision, after high-risk stories regularly needed more than two runs (§5) |
| Production-facing test, plan leg, done review, hold, epic walkthrough | A BMad maintainer's review: a clean check is one sample, so production work keeps human gates. The mechanism follows bmad-loop's actual checkpoint behaviour (§6). |
| R1–R12 in one `checks.ticket` home; second pass after approval; triage that never edits an approved story | A BMad maintainer's suggestion, adopted with two safeguards (§7) |
| Scoped re-runs, sweep, wording, what blocks, declined suggestions, stop | Six re-check rules from a BMad maintainer, after a story's GAP count grew with every round (§8) |
| Standing authority to take recommended options | The operator's standing instruction, after per-decision questions stalled the loop (§9) |
| Fresh review of park and sweep commits; sweep-written ADRs stay Proposed | Lessons: parks skip the review session, and a sweep shipped a fail-open check (`lessons.md` 16, 17) |
| In-build reviewer: detached tmux, PID file, deny rules, `--setting-sources project,local` | Lessons 9–11: a reviewer read the builder's plan, a hook broke allow rules, and a child reviewer died with its shell |
| Policy keys (`mark_done`, `thorough_review`, `trigger = "always"`, `[operator]`, `[sweep] auto = "never"`, project-independent probes, separate review vendor) | The production project's bmad-loop policy, and lessons 16, 18 and 28 |

## Credits

- [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) supplies Sofia, `bmad-customize`, the ticket tree and the memlog that this kit customizes, and its maintainers' review shaped §6–§8.
- Google's Elephant-Goldfish Model: [Introducing the Elephant-Goldfish Model plugin](https://opensource.googleblog.com/2026/10/introducing-elephant-goldfish-model-plugin.html) (Google Open Source Blog), and the repository [google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model) (Apache-2.0). The kit paraphrases its ideas and copies none of its text. EGM is not an officially supported Google product, and this kit is not affiliated with Google or BMad.

## Checking the kit

`python3 skills/bmad-delivery-kit/scripts/render_templates.py placeholders` lists every placeholder and flags any that has no default. To test a change, render with a real project's values (`render --values V.toml --out DIR`) and diff the result against that project's own override. Then render Sofia with the result, using the project's `_bmad/scripts/render_skill.py`.

## Versions

- **1.0.0**: the first extraction. The rules are the production project's checks ADR and delegation ADR, with all four of the latter's amendments folded in: the third run, production-facing gates, R1–R12 and the re-check rules.

## License

MIT. See [LICENSE](LICENSE).

---
name: bmad-delivery-kit
description: "Installs or upgrades a tested BMad delivery process in a BMad v7 project that runs bmad-loop: fresh-context explain-back and readiness checks before every story approval, risk-tiered run budgets, re-check rules, delegated approval by a coordinator session, operator actions that park stories, and human gates for production-facing stories. It writes a bmad-agent-po team override, two ADRs and bmad-loop policy keys. Use when the user says 'install the delivery kit', 'set up the delivery process', 'add fresh-context checks to Sofia', 'upgrade the delivery kit', or names bmad-delivery-kit."
---

# bmad-delivery-kit

This skill installs one delivery process into the BMad project you are working in, or upgrades an earlier install. `references/process.md` explains the process in plain words; read it first. `references/lessons.md` says why each rule exists, and `references/coordinator.md` covers how the coordinator session runs it.

`{skill-root}` is this skill's folder. `{project-root}` is the nearest folder above the working directory that holds `_bmad/`. "Scratch" means your scratchpad or a new temporary folder outside the project. The kit version is the output of `python3 {skill-root}/scripts/render_templates.py version`.

## What it writes

| File | How |
|---|---|
| `_bmad/custom/bmad-agent-po.toml` | merged through `bmad-customize`, keeping existing entries: `workflow.refine_before`, `workflow.validate_after`, two `workflow.checks.ticket` entries, and a header comment with the kit version |
| `_bmad/custom/bmad-delivery-kit.values.toml` | the parameter values used, for upgrades |
| `<adr-folder>/<N>-gate-story-approval-on-fresh-context-checks.md` | new ADR, status Proposed |
| `<adr-folder>/<N+1>-delegated-story-approval-and-standing-loop-authority.md` | new ADR, status Proposed |
| the ADR index, if the project keeps one | two rows |
| `.bmad-loop/policy.toml` | the snippet's keys merged in; machine-local |

## Ground rules

- Show a diff and wait for the user's explicit yes before every write. Never overwrite silently.
- Commit nothing and push nothing. The user commits.
- Never mark an ADR Accepted. Never mark a gate passed.
- Never edit the installed `bmad-agent-po` skill; the override is the only change to its behaviour.
- Never open files that `AGENTS.md` places off limits (credentials, secret stores, protected local environments) while inferring values. Copy no secret into any file.
- Run no hosted, deploy, provisioning or paid step. Install nothing yourself: when something is missing, say what to install.
- Edit TOML as text, line by line, so comments survive; `tomllib` only reads.
- Before the first write, copy each file you will change to scratch, so a failed verify can restore it.

## Install

### 1. Detect the setup, or refuse

Check everything below. Then report every failure together.

**Required.** If any of these is missing, stop and say what to install:

| Check | If missing, say |
|---|---|
| `{project-root}/_bmad/` with `config.toml`, `scripts/render_skill.py` and `scripts/memlog.py` | BMad v7 is not set up. Install the `bmad` skill and run its setup; for example `npx skills add bmad-code-org/BMAD-METHOD --skill bmad` (an example: check the command against the BMad docs). |
| A `bmad-agent-po/customize.toml` under a skill root (`.agents/skills/`, `.claude/skills/` or another root the project uses). Its `[workflow]` declares `refine_before`, `validate_after` and `checks.ticket`. | Sofia (`bmad-agent-po`) is missing or too old. Update BMad's method module. |
| In that skill, `references/ticket.md` contains `{{ workflow.refine_before }}`, "Self-review before the user sees it" and "After approval". `references/validate-checks.md` contains `## Ticket` and `{{ workflow.checks.ticket }}`. `references/validate.md` contains `{{ workflow.validate_after }}` and "Do not re-raise suggestions". | This `bmad-agent-po` differs from the one the kit was written against. Name the missing anchor, and do not install. |
| A `bmad-customize` skill | Install it with BMad's core tools. |
| `tickets.py`, in `_bmad/method/scripts/` or the PO skill's `scripts/` | The ticket tree is not set up. Run BMad's setup for the method module. |
| `bmad-loop --version` runs, and `.bmad-loop/policy.toml` exists | Install bmad-loop: ask the `bmad` skill to set up bmad-loop, or use the `bmad-loop-setup` skill, then run `bmad-loop init`. |
| `uv` on PATH, and a git repository | BMad's renderer runs through `uv`; the audit uses `git blame` and `git merge-base`. |

**Recommended.** Warn about these and continue:
- the `bmad-walkthrough` skill, which done reviews use;
- `bmad-loop-resolve`;
- an active initiative with a `tickets.toml`;
- `[stories] source = "tickets"`, which step 6 sets.

**Baseline.** Run `bmad-loop validate` now and save its full output (stdout and stderr) to scratch as the baseline. Step 7 compares against it. A failure here is not a refusal; report it.

**Existing install.** If `_bmad/custom/bmad-agent-po.toml` has a `# bmad-delivery-kit <version>, rendered` line, go to "Upgrade" instead. If it has a `checks.ticket` entry that starts "Pre-approval checks recorded" or "Readiness items R1–R12" but no such line, the process was added by hand. Tell the user, and treat it as an upgrade with no stored values.

### 2. Settle the parameters

`assets/parameters.md` lists every placeholder. Each one has a meaning, a default, an example and where to infer it from. Start from its Defaults block. Infer before you ask, using:
- `AGENTS.md` and `CLAUDE.md`, for banned tools, protected paths and resources, gates, test commands and the branch;
- `_bmad/config.toml`, for the project name and the output folder;
- `.bmad-loop/policy.toml`, for the session timeout, `[verify] commands`, adapters and `[scm] target_branch`;
- the ADR folder;
- `git`;
- the repository layout.

Specific rules:
- **ADR numbers.** Find the ADR folder: the one `AGENTS.md` or `docs/README.md` names, else the first of `docs/architecture/decisions/`, `docs/adr/`, `docs/decisions/` or `adr/` that exists. `CHECKS_ADR` is the highest `NNNN-` prefix + 1, and `DELEGATION_ADR` is + 2, both padded to the same width. With no `NNNN-` file, start at 0001, four digits. With no ADR folder, ask where to put one (recommend `docs/architecture/decisions/`). `ADR_DIR` is that folder, relative to the project root.
- **Branch and commit.** `DELIVERY_BRANCH` is the branch the loop commits to: `[scm] target_branch` if set, else the branch `AGENTS.md` names, else `git branch --show-current`. `ADOPTION_COMMIT` is `git rev-parse --short <DELIVERY_BRANCH>`.
- **Versions and dates.** `BMAD_LOOP_VERSION` comes from `bmad-loop --version`. Write every date as a literal `YYYY-MM-DD`: `ADOPTION_DATE` is today's date, and `CHECKS_DATE`, `DELEGATION_DATE`, `PRODUCTION_GATES_DATE` and `SESSION_TIMEOUT_DATE` repeat it unless the user adopted part of the process earlier. Never store `@today`; the renderer rejects it for every key but `RENDER_DATE`, so an upgrade's re-render cannot move a date the audit relies on.
- **Session timeout.** `SESSION_TIMEOUT_MIN` is `[limits] session_timeout_min` from the policy. If the key is unset, use bmad-loop's own default (90 minutes in 0.13.2; check `bmad-loop`'s policy docs for the installed version).
- **Ledger.** `DEFERRED_WORK_PATH` comes from `git ls-files '*deferred-work.md'`. Otherwise use `deferred-work.md` in the active initiative's folder.
- **Production set.** Infer `PRODUCTION_CODE`, `PUBLISHED_CONTRACTS`, `LOCAL_ONLY_SET` and `PRODUCTION_DECIDED_CASES` from the layout:
  - dependency manifests and lockfiles, and compiler and build config;
  - CI folders, and the scripts CI runs;
  - deployment and infrastructure folders, and local-environment folders;
  - fixture and test conventions;
  - API description files.

  The template already holds the generic decided cases. `PRODUCTION_DECIDED_CASES` holds only extra, project-specific ones, such as which real folders count as hosted configuration or local stack; add one for each borderline path you find, never one that restates or weakens a generic case. This set decides what delegation may approve, so step 4 shows it to the user on its own.
- **Adapters.** If the policy's dev and review adapters are the same vendor, recommend a different vendor for review, as `lessons.md` 18 explains. Do not force it.

Ask only what you cannot infer. Ask in one batch, each question with the answer you recommend. Write the values to `values.toml` in scratch, all as strings. No value may contain `{{`, `}}` or `'''`. `ENV_PROBES` is the exception: a probe that needs braces is merged by hand in step 6.

### 3. Render

```bash
python3 {skill-root}/scripts/render_templates.py render --values <scratch>/values.toml --out <scratch>/rendered
```

The script fails on a missing or `@infer` value, a surviving `{{`, or TOML that does not parse; fix the value and render again. Read the four rendered files.

If the ADR folder has its own template, such as `0000-template.md` with different headings, map the rendered ADRs onto it. Drop no content.

### 4. Merge the override through bmad-customize

Run `bmad-customize` for `bmad-agent-po`, team scope (`_bmad/custom/bmad-agent-po.toml`), from its Step 3. Read any existing override first, and use these merge rules:

- **No override yet:** the rendered file is the override.
- **An override exists:** keep every existing key, value and comment.
  - Add the rendered header comments after the file's first line.
  - Put the kit keys inside the existing `[workflow]` table. Never add a second `[workflow]` header. If the file uses a `[workflow.checks]` table, add `ticket = [...]` there.
  - `refine_before` and `validate_after` are strings, and an override's string replaces the skill's. If the project already sets one, keep its text in the same string: the kit's text first, then a line `<!-- project rules below, kept by bmad-delivery-kit -->`, then the project's text.
  - `checks.ticket` is a list, and an override's list appends to the skill's. Keep existing entries first, then the kit's two.

Build the merged file in scratch, then show:
1. `diff -u` of the current override against the merged file;
2. the parameter values;
3. the production artifact set and the decided cases, on their own, with a note that delegation never approves anything inside that set.

Wait for an explicit yes, then write. Write `_bmad/custom/bmad-delivery-kit.values.toml` in the same step, with a first line `# bmad-delivery-kit <version>: values for the rendered override; edit through the bmad-delivery-kit skill.`

Then run bmad-customize's verify: `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill <po-skill-dir> --project-root {project-root} --key workflow`. Confirm that the three keys hold the kit's text.

### 5. Write the two ADRs

Check that both numbers are still free. Write the rendered ADRs to these paths:
- `<adr-folder>/<CHECKS_ADR>-gate-story-approval-on-fresh-context-checks.md`;
- `<adr-folder>/<DELEGATION_ADR>-delegated-story-approval-and-standing-loop-authority.md`.

If the project keeps an ADR index, such as a table in `docs/architecture/README.md`, add both rows. Show the diff and wait for a yes. Both ADRs stay **Proposed**.

### 6. Merge the policy keys

Merge `rendered/bmad-loop-policy.snippet.toml` into `.bmad-loop/policy.toml` key by key. Set each key the snippet sets, and keep every other key and comment. In addition:
- Keep existing `extra_args`, which hold per-machine permission flags.
- If `REVIEW_ADAPTER` equals `DEV_ADAPTER` and `REVIEW_MODEL` is empty, leave the existing `[adapter.review]`, `[adapter.triage]` and `[adapter.retro]` tables as they are.
- Keep existing `[environment] probes`, unless one names a single local project or stack. Then recommend a project-independent probe (`lessons.md` 28).

Show the diff and wait for a yes. Tell the user the file is machine-local: it must be merged on every machine that runs the loop. If `REVIEW_ADAPTER` names a client whose hooks bmad-loop has not registered in this project (`bmad-loop validate` reports its profile, or the adapter differs from every adapter the policy used before), tell the user to run `bmad-loop init --cli <REVIEW_ADAPTER>`; do not run it yourself.

### 7. Verify

Run all of these. On a failure other than the `bmad-loop validate` exceptions below, restore the copies saved in scratch and report what failed.

```bash
python3 -c "import sys,tomllib; [tomllib.load(open(p,'rb')) for p in sys.argv[1:]]" \
  _bmad/custom/bmad-agent-po.toml _bmad/custom/bmad-delivery-kit.values.toml .bmad-loop/policy.toml
python3 {skill-root}/scripts/render_templates.py check-override _bmad/custom/bmad-agent-po.toml
uv run --no-cache _bmad/scripts/render_skill.py --project-root "{project-root}" --skill "<po-skill-dir>"
bmad-loop validate
```

`bmad-loop validate` must print a line containing `ok: policy OK`. Its `FAIL:` lines are accepted only when each is `git worktree is not clean`, which is expected because the kit's files are uncommitted, or appears word for word in the step-1 baseline. Any other `FAIL:` line is a failure. The render must not print `HALT:`. In the newest generation folder under `_bmad/render/bmad-agent-po/*/*/`, check that:
- `references/ticket.md` contains `## Fresh-context checks before approval`;
- `references/validate-checks.md` contains `Pre-approval checks recorded` and `Readiness items R1–R12`;
- `references/validate.md` contains `## Findings of a Ticket check on an approved story`;
- no `{{` remains in `references/`.

### 8. Record the kit version

The override's header comment `# bmad-delivery-kit <version>, rendered <date>; …` comes from the template, and `check-override` reads it back. The values file's first line names the same version. Confirm both match `render_templates.py version`.

### 9. Report

Report:
- each file written;
- the parameter values, marking which you inferred and which the user gave;
- the verify results.

Then list the user's next steps:
1. Read and accept both ADRs. Until ADR `<DELEGATION_ADR>` is Accepted, every approval goes to the user. Its standing authority (§9) and standing commits (§3) also start only then.
2. Commit the override, the values file, the ADRs and the index. The kit committed nothing.
3. Approve the risk relabel and the `hitl` reclassification (ADR §2, §4), then each epic's breakdown for execution.
4. Start the coordinator with the `/loop` prompt in `references/coordinator.md`, filled in, and set up the operator checklist.
5. Run the isolation probe once (`coordinator.md`).

## Upgrade

1. **Versions.** Read the installed version with `check-override`, and this kit's with `render_templates.py version`. If they are equal, report that and stop. If the installed one is newer, stop.
2. **What changed.** Read README.md's "Versions" for every version after the installed one: the rule changes and any new parameters. Infer or ask for the new parameters as in step 2. The other values come from `_bmad/custom/bmad-delivery-kit.values.toml`. Keep every stored date as it is; an upgrade never re-dates the process.
3. **Render** the new kit into scratch, as in step 3.
4. **Find local edits.** If this kit is a git checkout with a tag `v<installed>`, extract that version's `assets/` into scratch (`git -C <kit> archive v<installed> skills/bmad-delivery-kit | tar -x -C <scratch>/old`). Render it with the stored values, and diff the result against the project's three kit keys: those hunks are local edits. Without the old version, diff the project's keys against the new render. Treat every hunk the version notes do not explain as a possible local edit, and ask about it.
5. **Merge** the kit's changes and keep the local edits, under step 4's rules. Show the full diff and wait for a yes. Update the values file.
6. **ADRs.** Never rewrite an Accepted ADR's decision. For each rule change in the notes, append `## Amendment <date>: <title>`, status Proposed, to the ADR that owns the rule. Show the diff.
7. **Policy:** merge again as in step 6.
8. **Verify** as in step 7. The header now carries the new version.
9. **Report** as in step 9, and list the amendments the user must accept.

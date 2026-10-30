# Hard-won lessons

The kit was extracted from a production BMad project, and each lesson comes from running the process there. Each gives the event behind it, then the rule it led to and where that rule lives now.

## Checks and convergence

1. **A clean pass takes more than two runs.** High-risk stories regularly needed more than the two runs first allowed, some of them several rounds and a split. Each fresh reader finds something the last one missed. *Rule:* the coordinator may authorize one narrow third run (ADR D §5), and the stop rule ends it there (§8).
2. **Fix by class, not by instance.** On one story the explain-back GAP count rose with every round: each fix added text, and each new reader sampled new ambiguity. One sweep for every kind of gap found, plus cutting text nothing consumed, brought the next run down to a few undefined terms, then clean. *Rule:* the sweep before every re-run, and the wording rule.
3. **Not every GAP is a wrong build.** Blocking on every minor GAP kept stories in fix rounds. *Rule:* only gaps that could change what is built or how it is verified block; the rest are logged suggestions, and an unlabelled GAP still blocks.
4. **Re-reading everything after a small fix wastes runs.** *Rule:* scoped explain-back re-runs, with readiness always whole-story so contradictions are still caught.
5. **Know which fixes a confirmation run can clear.** A story's post-approval Ticket check failed because a "settle a builder choice" fix had been cleared by a readiness-only confirmation run. *Rule:* only "define a term already used" and "name the command for an existing observation" fixes may precede a confirmation run; settling a choice needs a fresh run of both checks.
6. **An item-4 point is a GAP even when marked MATCH.** Every term the reader could not define needs a fix line. *Rule:* item 3 and item 4 entries count as GAPs in the comparison.
7. **Run the Ticket check before announcing an approval.** Announcing first meant retracting. *Rule:* delegated approval commits only after a clean Ticket check (ADR D §1 step 4).
8. **Approval lines must cite the conditions that apply now.** After the production-gates rule added condition 8, approval lines had to say "conditions 3–8". *Rule:* the approval line names the conditions in force; update the line format with every amendment.

## Isolation

9. **Isolation must be enforced, not requested.** An in-build reviewer accepted every criterion, but it had read the builder's plan, which voided its review: its prompt said not to, its permissions allowed it. *Rule:* reviewers run isolated, not fenced: only their inputs, copied into a package folder outside the repository, under `--restricted --safe-mode --tools Read,Write` (`coordinator.md`, "Launching an in-build reviewer"). Deny rules were the first fix, and lessons 32 and 33 show why they were not enough.
10. **User-level hooks break exact allow rules.** A global hook that rewrote shell commands made exact `Bash(...)` allow rules miss, so the reviewer's commands were denied. *Rule:* launch reviewers with `--restricted`, which ignores user, project and local settings and their hooks. (`--setting-sources project,local` was the first fix; the isolated recipe replaced it.)
11. **Reviewers must outlive the shell that starts them.** A reviewer started as a background child of the builder's shell died with it and wrote nothing. *Rule:* start it in a detached tmux session that records its own PID first (`coordinator.md`).
12. **Prove isolation once.** Until a probe shows a child cannot see markers planted in the parent's context and in `AGENTS.md`/`CLAUDE.md`, isolation is assumed. *Rule:* the isolation probe follow-up in ADR C.

## Building and reviewing

13. **The post-build layers do the heavy lifting.** On the hardest story, the thorough review and an in-build fresh reviewer caught real defects after the evidence was fixed: an import-boundary check bypassable by a quote inside a regular-expression literal, then by a keyword used as a property name, and a conformance check rejecting valid output. Pre-approval checks cut gaps; they do not make a story "clean". *Rule:* every build gets the review session (`trigger = "always"`), high risk also gets the thorough inline review, and production work gets human gates.
14. **Prefer fail-closed rules for security checks.** Hand-written lexers kept failing open. *Rule:* use tokenization-free, fail-closed occurrence rules for boundary and purity checks.
15. **Stopping on every review finding is expensive.** One story's rules turned each post-build finding into a full stop and an evidence redo; it stopped repeatedly and spent many times its token budget. *Rule:* let the review loop fix in-scope findings itself and redo the evidence once at the end; only out-of-scope findings stop.
16. **Sweeps commit without story checks.** A deferred-work sweep shipped a security lexer that failed open and wrote an ADR as Accepted. *Rule:* `[sweep] auto = "never"`; the coordinator starts sweeps, runs a fresh review of every sweep commit, and marks any sweep-written ADR Proposed until reviewed.
17. **Parks skip the review session.** A story parked at `awaiting-operator` commits through the skip-review path. *Rule:* a fresh review of each park commit before every `bmad-loop confirm` batch.
18. **Use a different model to review.** *Rule:* the dev adapter builds; a different vendor's model reviews, triages and runs retrospectives.

## The human's place

19. **Per-story approval does not scale.** With hundreds of stories, per-story human approvals made the user the loop's bottleneck. *Rule:* delegated approval for clean, local, gate-free stories (ADR D §1).
20. **Per-decision questions stall the loop.** The operator found being asked about every choice too slow. *Rule:* the standing authority to take recommended options (ADR D §9); ask only for operator actions, hosted runs, gates, spend, legal matters, credentials, production approvals, or a choice with no defensible recommendation, batched with one notification.
21. **Every question comes with a recommendation.** *Rule:* each checklist item marks one option as recommended, with the reason.
22. **A clean check is one sample.** A BMad maintainer's review: an agent that misreads a story sees it as clean, so only a human can compare it with what they meant. Full automation suits throwaway proofs of concept, not production. *Rule:* production-facing stories get the user's approval, a plan review and a walkthrough (ADR D §6).
23. **Park instead of halt.** Reclassifying human steps as operator actions sharply cut the number of stories that stop the loop for a person. *Rule:* the `hitl` test (ADR D §2).

## bmad-loop mechanics

24. **`plan_checkpoint` on a refined ticket halts before any plan exists.** It asks to approve the story file, not the builder's plan. *Rule:* the coordinator's plan leg (ADR D §6 C).
25. **`done_checkpoint` never fires for a run's last story,** so never under `--max-stories 1` or `--story <ref>`, and `mark_done` is global. *Rule:* switch `mark_done` to `"never"` for one run, plus the hold (§6 D).
26. **A `built` plan already satisfies a dependent's `after`.** The next run could build on unreviewed code. *Rule:* the hold after each production-facing commit.
27. **Uncommitted coordinator lines pause the next run** at `ticket-tree` (the dirty-initiative gate). *Rule:* commit every bookkeeping line by pathspec before the next run starts.
28. **Environment probes tied to one local project break** when that project is recreated, for example after a container runtime restart changes its config hash. *Rule:* keep `[environment] probes` project-independent (the container daemon, not one stack).
29. **Hash only the story's own entry.** Hashing the whole `tickets.toml` would let any other story's edit void a check. *Rule:* the entry-block hash command in the override.

## Planning hygiene

30. **Check that every `after` is a real prerequisite.** Running Validate's "real prerequisite, not restated order" rule over one epic found several edges that only restated order; dropping the clear ones shortened the longest dependency chain substantially, which made a second build lane worthwhile.
31. **Write the checks in your own words.** Copying another project's prompts brings its licence along. *Rule:* the checks paraphrase EGM; no EGM text is copied.

## Learned after 1.0.0

32. **Read-only commands are approved without asking.** A build stopped because its reviewer ran `git status`, `git diff` and `git log`: Claude Code auto-approves read-only shell commands even under `--permission-mode dontAsk`, and a deny list is a blocklist (`sed -n p` read a plan, `echo */*` listed folders). *Rule:* the reviewer gets no shell at all (`--restricted`, `--tools Read,Write`).
33. **The repository leaks in through the git status snapshot.** A restricted reviewer whose working directory was inside the repository still started with Claude Code's git status snapshot (branch, changed files, recent commits). *Rule:* run it from a package folder outside the repository, with `--safe-mode`, which also keeps out `CLAUDE.md`, hooks and memory. The init event still lists built-in skills and plugins, but no Skill tool loads under `--tools Read,Write`. The probe's last step checks the starting context.
34. **Audit the log, never the model's own words.** A reviewer's report of what it read is not evidence. *Rule:* judge compliance from the `--output-format stream-json --verbose` log with a program that fails closed: every line parses; the init event's tools, `cwd`, `additional_directories` (empty, or only the package folder) and `permissionMode` are as launched, with every path compared after resolving symlinks; every `tool_use` is an allowed Read or Write; the last event is a successful result; and a call counts as refused only when a `permission_denied` event names it. Check the Claude Code version before launch and in the init event, and re-run the probe after every update.
35. **`resolve --no-interactive` plus `resume` rolls an escalated story back.** It reverts the story's tracked changes and re-implements from scratch, saving the attempt under `refs/attempt-preserve-dirty/…` (bmad-loop 0.13.2). *Rule:* to finish one step of a partial attempt, restore the files from that ref, do the step outside the loop under a dated decision, then use bmad-loop's `--restore-patch` procedure for the review and the commit.
36. **A story that keeps failing its checks may be doing two jobs.** When the failures come from one story both drafting something (a design, an evidence plan, a reviewer prompt) and building on it, fixes chase each other. *Rule:* at the stop, prefer a phase re-slice: one story drafts, the next reviews and builds on the draft, each with checks that can converge.
37. **Every build stop becomes a check.** Several stops came from what a story assumed about the tools or about existing outputs, which no reading of the text alone catches, and each fix was copied by hand into the next story. *Rule:* the known escalation classes K1–K6 run before approval and again before the build, and stories cite shared recipes by section instead of restating them. Add a K item whenever a new class of stop appears.

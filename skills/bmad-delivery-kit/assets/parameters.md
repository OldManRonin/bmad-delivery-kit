# Parameters

Every `{{PLACEHOLDER}}` in the kit's templates, what it means, its default, an example, and where the installer looks for it. `scripts/render_templates.py` reads the defaults from the `toml` block under "Defaults" below; that block is their only home. The installer writes the project's values to `_bmad/custom/bmad-delivery-kit.values.toml` (strings only), which overrides the defaults and is kept for upgrades.

Value syntax: `"@NAME"` copies another value, and `"@infer"` means the installer must supply a value; the render fails until it does, and also fails when such a value is blank. `"@today"` is allowed only for `RENDER_DATE`: every other date is stored as a literal `YYYY-MM-DD`, so an upgrade's re-render never moves a date the audit relies on. `{{NAME|cap}}` in a template capitalises the first letter. A template line holding only a placeholder whose value is empty is dropped.

## Identity and dates

| Placeholder | Meaning | Default | Example | Infer from |
|---|---|---|---|---|
| `KIT_VERSION` | Kit version, written into the override's header comment. | set by the script | `1.0.0` | `render_templates.py version` |
| `RENDER_DATE` | Date of this render. | `@today` | `2026-11-02` | clock |
| `CHECKS_ADR` | Number of the fresh-context checks ADR. | `@infer` | `0014` | next free number in the ADR folder, zero-padded like its neighbours |
| `DELEGATION_ADR` | Number of the delegated-approval ADR. | `@infer` | `0015` | `CHECKS_ADR` + 1 |
| `ADOPTION_DATE` | The date the process takes effect. Literal date. | `@infer` | `2026-11-02` | today's date at install, written literally |
| `CHECKS_DATE` | Approvals on or after it must have check records. Literal date. | `@ADOPTION_DATE` | `2026-11-02` | the adoption date, written literally; differs only for a staged adoption |
| `DELEGATION_DATE` | Medium and low labels count only if the user approved them on or after it; delegated approvals start then. Literal date. | `@ADOPTION_DATE` | `2026-11-02` | same |
| `PRODUCTION_GATES_DATE` | Approvals on or after it need a `Production-facing:` line. Literal date. | `@ADOPTION_DATE` | `2026-11-02` | same |
| `ADOPTION_COMMIT` | The delivery-branch commit the adoption lands on; stop-rule lines in its history are exempt. | `@infer` | `4f1c2ab` | `git rev-parse --short <DELIVERY_BRANCH>` before the adoption commit |
| `PRE_ADOPTION_APPROVALS` | Examples of approvals that predate the checks, inserted before a full stop as `, such as those of …` text. | `""` | `, such as those of 1.1 and 1.4` | approved stories in the memlogs; leave empty for a new project |
| `IN_FLIGHT_STORIES` | Stories mid-refinement at adoption that keep their logged runs, as `, such as …,` text. | `""` | `, such as 2.3,` | stories with check runs logged but not approved |

## Project shape

| Placeholder | Meaning | Default | Example | Infer from |
|---|---|---|---|---|
| `PROJECT_NAME` | Used in the coordinator's `/loop` prompt. | `this project` | `acme-billing` | `[core] project_name` in `_bmad/config.toml` |
| `DELIVERY_BRANCH` | The branch the loop commits to and delegated approvals happen on. | `@infer` | `main` | current branch, `[scm] target_branch`, `AGENTS.md` |
| `ADR_DIR` | The ADR folder, relative to the project root, with no trailing slash. | `@infer` | `docs/architecture/decisions` | the folder `AGENTS.md` or `docs/README.md` names, else `docs/architecture/decisions/`, `docs/adr/`, `docs/decisions/`, `adr/` |
| `DEFERRED_WORK_PATH` | The deferred-work ledger bmad-loop sweeps. | `@infer` | `docs/planning/initiative-acme-v1/deferred-work.md` | `find . -name deferred-work.md`, else the active initiative folder |
| `ARCHITECTURE_DOC` | Where approved contracts and boundaries are recorded, besides ADRs. | `the architecture document` | `` the architecture document (`docs/architecture/architecture.md`) `` | `docs/architecture/`, the epic files' `companions:` |
| `SOURCE_DIRS` | Directories whose change alters shipped source. | `@infer` | `` `src/` or `services/` `` | workspace manifests, top-level layout |
| `SOURCE_TERM` | The project's word for the identity of shipped source. | `source revision` | `source identity` | `AGENTS.md`, evidence docs |
| `UNIT_KINDS` | The kinds of unit a story can land in (R7). | `an app, a package, a service or a scripts folder` | a service, a library or `tools/` | layout |
| `ENV_NOUN` | A local working environment the checks name (singular; templates add `s`). | `environment` | `project` | local-environment docs |
| `HANDLES` | Names of those environments (plural noun; R9's label is this capitalised). | `environment handles` | `project handles` | local-environment docs |
| `PROTECTED_PATHS` | What a checker must never open, as text after "or". | `` any file `AGENTS.md` places off limits, such as a credential or secrets file `` | `` anything under `.dev-env/secrets/` `` | `AGENTS.md` credential rules, `.gitignore`d secret folders |
| `PROTECTED_RESOURCES` | What no story step may need (R9), besides a credential file. | `a shared, retained or production environment` | `a shared staging database` | `AGENTS.md` "never touch" rules |
| `BANNED_HOST_TOOLS` | Tools no command may need (R8). | `` a tool that `AGENTS.md` bans `` | `` host `npm` or `python` `` | `AGENTS.md` "never run" rules |
| `SESSION_TIMEOUT_MIN` | bmad-loop's session timeout, for R11 and the policy. | `@infer` | `180` | `[limits] session_timeout_min`; if unset, bmad-loop's own default (90 in 0.13.2) |
| `SESSION_TIMEOUT_DATE` | The date that timeout was read. Literal date. | `@ADOPTION_DATE` | `2026-11-02` | the adoption date, written literally |

## Gates and production

| Placeholder | Meaning | Default | Example | Infer from |
|---|---|---|---|---|
| `GATES_LIST` | Every formal gate, for the reserved-area rule (approval condition 5). | `every release, security, compliance or sign-off gate the project's documents define` | `the release gate, the SOC 2 evidence gate and the pen-test sign-off` | `AGENTS.md` gate rules, PRD, delivery plan |
| `GATES_SHORT` | The same, short, for R3's "nothing claims to pass …". | `a formal gate` | `the release gate or a SOC 2 control` | same |
| `LEGAL_RULE_EXAMPLE` | A recorded legal rule whose exact implementation is not a legal matter, as `, such as …,` text. | `""` | `, such as ADR 0005,` | a licensing or data-policy ADR |
| `PRODUCTION_CODE` | Shipped code, with its exceptions, after "code under". | `@infer` | `` `src/`, except in `fixtures/` or `test/` directories and in `*.test.*` files `` | layout, test conventions |
| `PUBLISHED_CONTRACTS` | What counts as a published contract. | see Defaults | `the REST API's request, response and error shapes, the OpenAPI document and the webhook payloads` | API docs, OpenAPI files, SDKs |
| `LOCAL_ONLY_SET` | What a local-only story may change. | see Defaults | `` local tooling (`scripts/`, `docker/dev/`), fixture code, tests, ADRs, documentation or planning files `` | layout |
| `PRODUCTION_DECIDED_CASES` | Extra settled cases for this project only, one Markdown bullet per line, such as which real paths count as hosted configuration. The template already holds the generic cases (manifests, CI, hosted configuration, fixtures, test files, the local stack, design that fixes a production shape, work chosen during the build); add cases, never restate or weaken those. Empty drops the line. | `""` | ``- **Hosted configuration here:** anything under `deploy/` except `deploy/dev/`.`` | manifests, CI folders, infra folders |

## Agents and the loop

| Placeholder | Meaning | Default | Example | Infer from |
|---|---|---|---|---|
| `COORDINATOR_AGENT` | What the coordinator is, after "the". | `agent session` | `Claude session` | the harness running the kit |
| `FRESH_AGENT_HOWTO` | One sentence: how to start a brand-new, non-fork subagent in this harness. | the Claude Code sentence | `In Codex that is a new codex exec process started with only the brief on stdin.` | the harness |
| `DEV_ADAPTER` | bmad-loop adapter for the dev session. | `@infer` | `codex` | `[adapter] name` |
| `DEV_AGENT` | How the ADR names the builder. | `@DEV_ADAPTER` | `Codex` | same |
| `REVIEW_ADAPTER` | bmad-loop adapter for review, triage and retrospective sessions. | `@DEV_ADAPTER` | `claude` | `[adapter.review] name`; recommend a different vendor from dev |
| `REVIEW_AGENT` | How the ADR names the reviewer. | `@REVIEW_ADAPTER` | `Claude Opus` | same |
| `REVIEW_MODEL` | Model for those sessions; empty is the CLI default. | `""` | `opus` | `[adapter.review] model` |
| `VERIFY_COMMANDS` | `[verify] commands`, as a TOML array. | `@infer` | `["make test", "make lint"]` | `[verify] commands`, `AGENTS.md` test commands |
| `ENV_PROBES` | `[environment] probes`, as a TOML array. Keep them project-independent. | `[]` | `["docker info --format {{.ServerVersion}}"]` wrapped as TOML | `[environment] probes` |
| `BMAD_LOOP_VERSION` | The bmad-loop version the ADR's loop facts were checked against. | `@infer` | `0.13.2` | `bmad-loop --version` |

Note on `ENV_PROBES`: a value containing `{{` or `}}` (such as a Docker format string) cannot pass through the renderer, which rejects any surviving braces. Merge such a probe into the policy by hand and set `ENV_PROBES = "[]"`.

## Defaults

```toml
KIT_VERSION = "1.0.0"
RENDER_DATE = "@today"
CHECKS_ADR = "@infer"
DELEGATION_ADR = "@infer"
ADOPTION_DATE = "@infer"
CHECKS_DATE = "@ADOPTION_DATE"
DELEGATION_DATE = "@ADOPTION_DATE"
PRODUCTION_GATES_DATE = "@ADOPTION_DATE"
ADOPTION_COMMIT = "@infer"
PRE_ADOPTION_APPROVALS = ""
IN_FLIGHT_STORIES = ""
PROJECT_NAME = "this project"
DELIVERY_BRANCH = "@infer"
ADR_DIR = "@infer"
DEFERRED_WORK_PATH = "@infer"
ARCHITECTURE_DOC = "the architecture document"
SOURCE_DIRS = "@infer"
SOURCE_TERM = "source revision"
UNIT_KINDS = "an app, a package, a service or a scripts folder"
ENV_NOUN = "environment"
HANDLES = "environment handles"
PROTECTED_PATHS = "any file `AGENTS.md` places off limits, such as a credential or secrets file"
PROTECTED_RESOURCES = "a shared, retained or production environment"
BANNED_HOST_TOOLS = "a tool that `AGENTS.md` bans"
SESSION_TIMEOUT_MIN = "@infer"
SESSION_TIMEOUT_DATE = "@ADOPTION_DATE"
GATES_LIST = "every release, security, compliance or sign-off gate the project's documents define"
GATES_SHORT = "a formal gate"
LEGAL_RULE_EXAMPLE = ""
PRODUCTION_CODE = "@infer"
PUBLISHED_CONTRACTS = "an endpoint's request, response or error shape, an API description document, a generated client, a CLI's commands and output, or an agent tool"
LOCAL_ONLY_SET = "local tooling, test fixtures, tests, ADRs, documentation or planning files"
PRODUCTION_DECIDED_CASES = ""
COORDINATOR_AGENT = "agent session"
FRESH_AGENT_HOWTO = "In Claude Code that is a new Agent call with a non-fork type such as `general-purpose`."
DEV_ADAPTER = "@infer"
DEV_AGENT = "@DEV_ADAPTER"
REVIEW_ADAPTER = "@DEV_ADAPTER"
REVIEW_AGENT = "@REVIEW_ADAPTER"
REVIEW_MODEL = ""
VERIFY_COMMANDS = "@infer"
ENV_PROBES = "[]"
BMAD_LOOP_VERSION = "@infer"
```

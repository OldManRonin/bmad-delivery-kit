#!/usr/bin/env python3
"""Render the bmad-delivery-kit templates with one values file.

Standard library only, Python 3.11+. The defaults live in one place: the ```toml block
under "## Defaults" in assets/parameters.md. A values file overrides them.

  render_templates.py render --values V.toml --out DIR     render all four templates into DIR
  render_templates.py check-override FILE                   parse an override and check the kit keys
  render_templates.py placeholders                          list every placeholder the templates use
  render_templates.py version                               print the kit version

A value may be "@NAME" (a copy of another value). "@today" is allowed only for RENDER_DATE,
so that re-rendering never moves a date the audit relies on: every other date is a
literal YYYY-MM-DD. A value left at "@infer", or one whose default is "@infer" and that
resolves blank, is an error: the installer must supply it. VERIFY_COMMANDS must be a
non-empty TOML array of strings. Every placeholder must have a value, no rendered file may
keep a `{{` or `}}`, and the rendered override and policy snippet must parse with tomllib.
A template line that holds only a placeholder whose value is empty is dropped.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import tomllib
from pathlib import Path

KIT_VERSION = "1.0.0"

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
TEMPLATES = {
    "bmad-agent-po.override.toml": ASSETS / "bmad-agent-po.override.toml.tmpl",
    "adr-fresh-context-checks.md": ASSETS / "adr-fresh-context-checks.md.tmpl",
    "adr-delegated-approval.md": ASSETS / "adr-delegated-approval.md.tmpl",
    "bmad-loop-policy.snippet.toml": ASSETS / "bmad-loop-policy.snippet.toml",
}
PLACEHOLDER = re.compile(r"\{\{([A-Z][A-Z0-9_]*)(\|cap)?\}\}")
LONE_PLACEHOLDER = re.compile(r"^\{\{([A-Z][A-Z0-9_]*)\}\}\n", re.M)
ANY_BRACES = re.compile(r"\{\{|\}\}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_KEYS = {"ADOPTION_DATE", "CHECKS_DATE", "DELEGATION_DATE", "PRODUCTION_GATES_DATE", "SESSION_TIMEOUT_DATE", "RENDER_DATE"}
KIT_KEYS = ("refine_before", "validate_after")
KIT_CHECK_TITLES = ("Pre-approval checks recorded", "Readiness items R1–R12")
AUTO = {"KIT_VERSION", "RENDER_DATE"}


class KitError(Exception):
    pass


def load_defaults() -> dict[str, str]:
    text = (ASSETS / "parameters.md").read_text(encoding="utf-8")
    match = re.search(r"^## Defaults\n.*?^```toml\n(.*?)^```", text, re.S | re.M)
    if not match:
        raise KitError("parameters.md has no ```toml block under '## Defaults'")
    return _strings(tomllib.loads(match.group(1)), "parameters.md defaults")


def _strings(data: dict, label: str) -> dict[str, str]:
    out = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise KitError(f"{label}: {key} must be a string")
        out[key] = value
    return out


def _no_today(values: dict[str, str], label: str) -> None:
    bad = sorted(key for key, value in values.items() if value == "@today" and key != "RENDER_DATE")
    if bad:
        raise KitError(f"{label}: '@today' is allowed only for RENDER_DATE; write a literal YYYY-MM-DD for {', '.join(bad)}")


def resolve(values: dict[str, str], today: str) -> dict[str, str]:
    resolved: dict[str, str] = {}

    def get(name: str, seen: tuple[str, ...]) -> str:
        if name in resolved:
            return resolved[name]
        if name in seen:
            raise KitError(f"circular value reference: {' -> '.join(seen + (name,))}")
        if name not in values:
            raise KitError(f"no value for {name}")
        raw = values[name]
        if raw == "@infer":
            raise KitError(f"{name} is still @infer: the installer must supply it")
        if raw == "@today":
            value = today
        elif re.fullmatch(r"@[A-Z][A-Z0-9_]*", raw):
            value = get(raw[1:], seen + (name,))
        else:
            value = raw
        resolved[name] = value
        return value

    for name in values:
        get(name, ())
    return resolved


def validate_values(values: dict[str, str], defaults: dict[str, str]) -> None:
    blank = sorted(key for key, default in defaults.items() if default == "@infer" and not values[key].strip())
    if blank:
        raise KitError(f"blank value for a required parameter: {', '.join(blank)}")
    for key in sorted(DATE_KEYS & set(values)):
        if not DATE.fullmatch(values[key]):
            raise KitError(f"{key} must be a literal YYYY-MM-DD date, got {values[key]!r}")
    try:
        commands = tomllib.loads(f"v = {values['VERIFY_COMMANDS']}")["v"]
    except tomllib.TOMLDecodeError as error:
        raise KitError(f"VERIFY_COMMANDS is not a TOML array: {error}") from error
    if not isinstance(commands, list) or not commands or not all(isinstance(c, str) and c.strip() for c in commands):
        raise KitError("VERIFY_COMMANDS must be a non-empty TOML array of non-empty strings")


def render_text(text: str, values: dict[str, str], label: str) -> str:
    missing = sorted({m.group(1) for m in PLACEHOLDER.finditer(text) if m.group(1) not in values})
    if missing:
        raise KitError(f"{label}: no value for {', '.join(missing)}")
    # A line that is only a placeholder with an empty value disappears with its newline.
    text = LONE_PLACEHOLDER.sub(lambda m: "" if values[m.group(1)] == "" else m.group(0), text)

    def sub(m: re.Match) -> str:
        value = values[m.group(1)]
        return value[:1].upper() + value[1:] if m.group(2) else value

    out = PLACEHOLDER.sub(sub, text)
    if ANY_BRACES.search(out):
        raise KitError(f"{label}: a '{{{{' or '}}}}' survived rendering")
    return out


def check_override_text(text: str, label: str) -> dict:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise KitError(f"{label}: TOML does not parse: {error}") from error
    workflow = data.get("workflow", {})
    for key in KIT_KEYS:
        if not isinstance(workflow.get(key), str) or not workflow[key].strip():
            raise KitError(f"{label}: workflow.{key} missing or empty")
    checks = workflow.get("checks", {}).get("ticket", [])
    if not isinstance(checks, list):
        raise KitError(f"{label}: workflow.checks.ticket is not a list")
    for title in KIT_CHECK_TITLES:
        if sum(1 for item in checks if isinstance(item, str) and item.startswith(title)) != 1:
            raise KitError(f"{label}: workflow.checks.ticket needs exactly one entry starting {title!r}")
    match = re.search(r"^# bmad-delivery-kit (\S+), rendered (\S+);", text, re.M)
    if not match:
        raise KitError(f"{label}: no '# bmad-delivery-kit <version>, rendered <date>;' header comment")
    return {"kit_version": match.group(1), "rendered": match.group(2)}


def cmd_render(args: argparse.Namespace) -> None:
    defaults = load_defaults()
    _no_today(defaults, "parameters.md defaults")
    supplied = _strings(tomllib.loads(Path(args.values).read_text(encoding="utf-8")), args.values) if args.values else {}
    _no_today(supplied, args.values or "values")
    unknown = sorted(set(supplied) - set(defaults) - AUTO)
    if unknown:
        raise KitError(f"values file sets unknown parameters: {', '.join(unknown)}")
    if supplied.get("KIT_VERSION", KIT_VERSION) != KIT_VERSION:
        raise KitError(f"values file pins KIT_VERSION {supplied['KIT_VERSION']}, this kit is {KIT_VERSION}")
    today = args.today or datetime.date.today().isoformat()
    merged = defaults | supplied | {"KIT_VERSION": KIT_VERSION}
    merged.setdefault("RENDER_DATE", "@today")
    values = resolve(merged, today)
    validate_values(values, defaults)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    for name, path in TEMPLATES.items():
        text = path.read_text(encoding="utf-8")
        used |= {m.group(1) for m in PLACEHOLDER.finditer(text)}
        if name.endswith(".toml"):
            bad = sorted({m.group(1) for m in PLACEHOLDER.finditer(text) if "'''" in values.get(m.group(1), "")})
            if bad:
                raise KitError(f"{name}: values contain ''' and would break a TOML literal string: {', '.join(bad)}")
        rendered = render_text(text, values, name)
        if name == "bmad-agent-po.override.toml":
            check_override_text(rendered, name)
        elif name.endswith(".toml"):
            try:
                tomllib.loads(rendered)
            except tomllib.TOMLDecodeError as error:
                raise KitError(f"{name}: TOML does not parse: {error}") from error
        (out_dir / name).write_text(rendered, encoding="utf-8")
        print(f"rendered {out_dir / name}")
    unused = sorted(set(defaults) - used)
    if unused:
        print(f"note: parameters no template uses (coordinator.md only): {', '.join(unused)}")


def cmd_check_override(args: argparse.Namespace) -> None:
    info = check_override_text(Path(args.file).read_text(encoding="utf-8"), args.file)
    print(f"ok: parses; kit keys present; kit {info['kit_version']} rendered {info['rendered']}")


def cmd_placeholders(_: argparse.Namespace) -> None:
    names: dict[str, set[str]] = {}
    for name, path in TEMPLATES.items():
        for m in PLACEHOLDER.finditer(path.read_text(encoding="utf-8")):
            names.setdefault(m.group(1), set()).add(name)
    defaults = load_defaults()
    for key in sorted(names):
        flag = "" if key in defaults or key in AUTO else "  <-- no default in parameters.md"
        print(f"{key}: {', '.join(sorted(names[key]))}{flag}")
    for key in sorted(set(defaults) - set(names) - AUTO):
        print(f"{key}: (no template; coordinator.md only)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("render")
    p.add_argument("--values", help="values TOML; every key a string")
    p.add_argument("--out", required=True)
    p.add_argument("--today", help="override the render date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_render)
    p = sub.add_parser("check-override")
    p.add_argument("file")
    p.set_defaults(func=cmd_check_override)
    sub.add_parser("placeholders").set_defaults(func=cmd_placeholders)
    sub.add_parser("version").set_defaults(func=lambda _: print(KIT_VERSION))
    args = parser.parse_args()
    try:
        args.func(args)
    except (KitError, OSError, tomllib.TOMLDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

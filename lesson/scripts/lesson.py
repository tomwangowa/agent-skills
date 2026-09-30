#!/usr/bin/env python3
"""lesson: capture and load lessons learned. Standard library only.

Deterministic half of the /lesson skill. Drafting and asking for
confirmation live in SKILL.md; this script validates, reads and writes files.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_DIR / "config.json"
DEFAULTS = {"cap_global": 20, "cap_project": 10}
RULE_MAX = 120
CONFLICT_RE = re.compile(r"\(\d+\)|conflicted copy", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(
        r"(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*\S{8,}",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------- config

def config_path():
    return Path(os.environ.get("LESSON_CONFIG") or DEFAULT_CONFIG)


def load_config():
    """Return the merged config, or None when missing or unusable."""
    path = config_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or not raw.get("lessons_dir"):
        return None
    cfg = dict(DEFAULTS)
    cfg.update(raw)
    cfg["lessons_dir"] = Path(os.path.expanduser(str(raw["lessons_dir"])))
    for key in ("cap_global", "cap_project"):
        try:
            cfg[key] = int(cfg[key])
        except (TypeError, ValueError):
            cfg[key] = DEFAULTS[key]
    return cfg


def detect_project():
    """Git root folder name; the current folder name outside git."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).name
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().name


# ----------------------------------------------------------- frontmatter

def quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    return value


def split_frontmatter(text):
    """Return (meta dict, body) or (None, text) when there is no block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    meta = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[index + 1:])
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = unquote(value)
    return None, text


def valid_meta(meta):
    if not meta.get("rule"):
        return False
    if meta.get("scope") not in ("global", "project"):
        return False
    if meta.get("status") not in ("active", "retired"):
        return False
    if not DATE_RE.match(meta.get("created", "")):
        return False
    if meta["scope"] == "project" and not meta.get("project"):
        return False
    return True


def scan(lessons_dir):
    """Return (valid lessons, unparsable count, conflict-copy count)."""
    valid, bad, conflicts = [], 0, 0
    for path in sorted(lessons_dir.iterdir()):
        if not path.is_file() or path.suffix != ".md":
            continue
        if path.name.startswith((".", "_")):
            continue
        if CONFLICT_RE.search(path.name):
            conflicts += 1
            continue
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            meta = None
        if meta is None or not valid_meta(meta):
            bad += 1
            continue
        meta["file"] = path.name
        valid.append(meta)
    return valid, bad, conflicts


# ------------------------------------------------------------ validation

def clip(rule):
    """Guard the session context against over-long hand-edited or synced rules."""
    return rule if len(rule) <= RULE_MAX else rule[:RULE_MAX - 1] + "…"


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:50]
    return slug.strip("-") or "lesson"


def validate_entry(entry):
    """Return a normalised entry dict or raise ValueError."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    rule = str(entry.get("rule", "")).strip()
    if not rule:
        raise ValueError("rule is empty")
    if "\n" in rule or "\r" in rule:
        raise ValueError("rule must be a single line")
    if len(rule) > RULE_MAX:
        raise ValueError(f"rule is {len(rule)} chars; limit is {RULE_MAX}")
    scope = entry.get("scope")
    if scope not in ("global", "project"):
        raise ValueError("scope must be 'global' or 'project'")
    project = str(entry.get("project") or "").strip()
    if scope == "project" and not project:
        raise ValueError("project is required when scope is 'project'")
    if "\n" in project or "\r" in project:
        raise ValueError("project must be a single line")
    by = str(entry.get("by") or "claude")
    if not re.fullmatch(r"[a-z0-9-]+", by):
        raise ValueError("by must match [a-z0-9-]+")
    why = str(entry.get("why") or "")
    background = str(entry.get("background") or "")
    for field, text in (("rule", rule), ("why", why), ("background", background)):
        if any(rx.search(text) for rx in SECRET_RES):
            raise ValueError(f"{field} looks like it contains a secret")
    return {
        "rule": rule, "scope": scope,
        "project": project if scope == "project" else "",
        "by": by, "why": why, "background": background,
        "slug": entry.get("slug") or "",
    }


def render(entry, created, migrated_from=None):
    lines = ["---", f"rule: {quote(entry['rule'])}", f"scope: {entry['scope']}"]
    if entry["scope"] == "project":
        lines.append(f"project: {quote(entry['project'])}")
    lines += ["status: active", f"created: {created}", f"by: {quote(entry['by'])}"]
    if migrated_from:
        lines.append(f"migrated_from: {quote(migrated_from)}")
    lines += [
        "---", "",
        "## 為什麼", entry["why"], "",
        "## 背景", entry["background"], "",
    ]
    return "\n".join(lines)


def write_lesson(lessons_dir, entry, created, migrated_from=None):
    """Write a new lesson file; never overwrite, never create the folder."""
    if not lessons_dir.is_dir():
        raise ValueError(
            f"lessons_dir does not exist: {lessons_dir} "
            "(is the sync folder mounted?)"
        )
    text = render(entry, created, migrated_from)
    base = f"{created}-{slugify(entry['slug'])}"
    number = 1
    while True:
        name = f"{base}.md" if number == 1 else f"{base}-{number}.md"
        try:
            with open(lessons_dir / name, "x", encoding="utf-8") as handle:
                handle.write(text)
            return lessons_dir / name
        except FileExistsError:
            number += 1


def read_json(path):
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def need_config():
    cfg = load_config()
    if cfg is None:
        print("lessons: 尚未設定，請執行 /lesson setup", file=sys.stderr)
        sys.exit(1)
    return cfg


# -------------------------------------------------------------- commands

def cmd_digest(args):
    try:
        return _digest(args)
    except Exception as exc:  # never break session start, never stay silent
        print(f"lessons: ⚠ 載入失敗（{type(exc).__name__}）")
        return 0


def _digest(args):
    cfg = load_config()
    if cfg is None:
        print("lessons: 尚未設定，請執行 /lesson setup")
        return 0
    try:
        valid, bad, conflicts = scan(cfg["lessons_dir"])
    except OSError:
        print("lessons: ⚠ 讀不到資料夾")
        return 0
    found = len(valid) + bad + conflicts
    active = [m for m in valid if m["status"] == "active"]
    if found and not active:
        print(f"lessons: ⚠ 找到 {found} 個檔案，載入 0 條")
        return 0

    project = args.project or detect_project()

    def pick(scope, cap):
        items = [
            m for m in active
            if m["scope"] == scope
            and (scope == "global" or m["project"] == project)
        ]
        items.sort(key=lambda m: (m["created"], m["file"]), reverse=True)
        return items[:cap], len(items) > cap

    globals_, g_over = pick("global", cfg["cap_global"])
    projects_, p_over = pick("project", cfg["cap_project"])

    parts = [f"lessons: 全域 {len(globals_)} 條、專案 {len(projects_)} 條"]
    if bad:
        parts.append(f"⚠ 略過 {bad} 個")
    if conflicts:
        parts.append(f"⚠ 略過 {conflicts} 個疑似衝突副本")
    if g_over or p_over:
        parts.append("⚠ 已超過上限，請執行 /lesson review")
    print(" ".join(parts))
    for item in globals_:
        print(f"- [全域] {clip(item['rule'])}")
    for item in projects_:
        print(f"- [專案] {clip(item['rule'])}")
    return 0


def cmd_add(args):
    cfg = need_config()
    try:
        entry = validate_entry(read_json(args.json))
        if args.dry_run:
            print("ok")
            return 0
        path = write_lesson(cfg["lessons_dir"], entry, date.today().isoformat())
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


def cmd_list(args):
    cfg = need_config()
    try:
        valid, bad, conflicts = scan(cfg["lessons_dir"])
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    project = args.project or detect_project()
    active = [m for m in valid if m["status"] == "active"]
    retired = len(valid) - len(active)
    g = [m for m in active if m["scope"] == "global"]
    p = [m for m in active if m["scope"] == "project"]
    if args.project:
        p = [m for m in p if m["project"] == args.project]
    print(f"[全域] {len(g)}/{cfg['cap_global']}")
    for m in g:
        print(f"  {m['file']}  {m['rule']}")
    mine = [m for m in p if m["project"] == project]
    print(f"[專案:{project}] {len(mine)}/{cfg['cap_project']}")
    for m in p:
        print(f"  {m['file']}  ({m['project']}) {m['rule']}")
    print(f"retired: {retired}  unparsable: {bad}  conflict-copies: {conflicts}")
    return 0


def cmd_retire(args):
    cfg = need_config()
    name = args.file
    if "/" in name or "\\" in name or not name.endswith(".md"):
        print("error: give a lesson file name, not a path", file=sys.stderr)
        return 2
    path = cfg["lessons_dir"] / name
    if not path.is_file():
        print(f"error: no such lesson: {name}", file=sys.stderr)
        return 1
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        print("error: no frontmatter", file=sys.stderr)
        return 1
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    status_at = next(
        (i for i in range(1, end or 0) if lines[i].startswith("status:")), None
    )
    if end is None or status_at is None:
        print("error: no status field", file=sys.stderr)
        return 1
    if unquote(lines[status_at].partition(":")[2]) == "retired":
        print("error: already retired", file=sys.stderr)
        return 1
    lines[status_at] = "status: retired"
    extra = [f"retired_at: {date.today().isoformat()}"]
    if args.reason:
        extra.append(f"retired_reason: {quote(args.reason.replace(chr(10), ' '))}")
    lines[end:end] = extra
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print(f"retired: {name}")
    return 0


def memory_feedback_files(src):
    for path in sorted(Path(src).expanduser().glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            continue
        meta = meta or {}
        if path.name.startswith("feedback_") or meta.get("type") == "feedback":
            yield path, meta, body.strip()


def cmd_migrate(args):
    cfg = need_config()
    if not Path(args.src).expanduser().is_dir():
        print(f"error: --from is not a folder: {args.src}", file=sys.stderr)
        return 1
    lessons_dir = cfg["lessons_dir"]
    try:
        valid, _, _ = scan(lessons_dir)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    done = {m.get("migrated_from") for m in valid if m.get("migrated_from")}
    sources = {p.name: (p, m, b) for p, m, b in memory_feedback_files(args.src)}

    if args.plan:
        rows = [
            {
                "file": name, "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "body": body, "already_migrated": name in done,
            }
            for name, (_, meta, body) in sources.items()
        ]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    try:
        mapping = read_json(args.apply)
    except (ValueError, OSError) as exc:
        print(f"error: cannot read mapping: {exc}", file=sys.stderr)
        return 2
    if not isinstance(mapping, list):
        print("error: mapping must be a JSON list of objects", file=sys.stderr)
        return 2
    prepared, errors = [], []
    for position, row in enumerate(mapping, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {position}: not a JSON object")
            continue
        name = row.get("file")
        if name not in sources:
            errors.append(f"{name}: not a feedback file in {args.src}")
            continue
        if name in done:
            continue
        _, meta, body = sources[name]
        try:
            entry = validate_entry({
                "rule": row.get("rule"), "scope": row.get("scope"),
                "project": row.get("project"), "by": "user",
                "why": meta.get("description", ""), "background": body,
                "slug": name.removesuffix(".md").removeprefix("feedback_")
                .replace("_", "-"),
            })
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        created = datetime.fromtimestamp(sources[name][0].stat().st_mtime)
        prepared.append((name, entry, created.date().isoformat()))
    if errors:
        print("nothing written:\n" + "\n".join(errors), file=sys.stderr)
        return 2
    try:
        for name, entry, created in prepared:
            write_lesson(lessons_dir, entry, created, migrated_from=name)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"written: {len(prepared)}  skipped(already migrated): "
          f"{len(mapping) - len(prepared)}")
    return 0


def cmd_setup(args):
    path = config_path()
    if path.exists() and not args.force:
        print(f"error: {path} already exists (use --force)", file=sys.stderr)
        return 1
    target = Path(os.path.expanduser(args.dir))
    if not target.is_dir():
        if not args.create:
            print(f"error: {target} does not exist (use --create)", file=sys.stderr)
            return 1
        target.mkdir(parents=True)
    stored = args.dir if args.dir.startswith("~") else os.path.abspath(args.dir)
    path.write_text(
        json.dumps({"lessons_dir": stored, **DEFAULTS}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"configured: {path}")
    return 0


def cmd_snippet(_args):
    template = (SKILL_DIR / "templates" / "entry-snippet.md").read_text(encoding="utf-8")
    script = f"python3 {shlex.quote(str(Path(__file__).resolve()))}"
    print(template.replace("{{SCRIPT}}", script), end="")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="lesson")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("digest")
    p.add_argument("--project")
    p.set_defaults(func=cmd_digest)

    p = sub.add_parser("add")
    p.add_argument("--json", required=True, help="entry JSON file, or - for stdin")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list")
    p.add_argument("--project")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("retire")
    p.add_argument("file")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_retire)

    p = sub.add_parser("migrate")
    p.add_argument("--from", dest="src", required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--apply", metavar="MAPPING_JSON")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("setup")
    p.add_argument("--dir", required=True)
    p.add_argument("--create", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("snippet")
    p.set_defaults(func=cmd_snippet)
    return parser


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

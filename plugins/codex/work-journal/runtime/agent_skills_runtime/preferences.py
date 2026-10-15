"""Load personal rules without modifying installed defaults; serialize confirmed edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

MODULE_NAME = re.compile(r"[\w.-]+\.md")
RULE_BLOCK = re.compile(
    r"^## Rule[ \t]*\n(?:(?!^## ).)*?^```text[ \t]*\n(.*?)^```", re.DOTALL | re.MULTILINE)


def _module_name(name: str) -> str:
    if not MODULE_NAME.fullmatch(name) or name == "INDEX.md" or name.startswith("."):
        raise ValueError(f"Invalid module filename: {name}")
    return name


def _read(path: Path) -> str:
    if path.is_symlink():
        raise ValueError(f"Symlink rule is not allowed: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty rule file: {path}")
    return text


def _personal_dir(config_root: Path) -> Path:
    from .config import require_external_personal_path
    path = config_root / "preferences"
    require_external_personal_path(path)
    if path.is_symlink():
        raise ValueError(f"Symlink preferences directory is not allowed: {path}")
    return path


def _index(path: Path, warnings: list[str]) -> list[str]:
    try:
        text = _read(path)
    except (OSError, ValueError) as error:
        warnings.append(f"Cannot read {path}: {error}")
        return []
    names = []
    for line in text.splitlines():
        cells = line.strip().strip("|").split("|")
        if not line.lstrip().startswith("|") or len(cells) < 2:
            continue
        name = cells[1].strip().strip("`").strip()
        if name == "File" or set(name) <= set("-: "):
            continue
        try:
            _module_name(name)
            if name == "control-return.md":
                raise ValueError("control-return.md belongs to its own hook")
        except ValueError as error:
            warnings.append(f"{path}: {error} (invalid INDEX.md entry)")
            continue
        if name not in names:
            names.append(name)
    if not names and not warnings:
        warnings.append(f"{path} lists no modules; rules were not loaded")
    return names


def load_preferences(default_dir: Path, config_root: Path) -> tuple[str, list[str]]:
    """Overlay whole modules; a broken override stays inactive rather than falling back."""
    warnings: list[str] = []
    names = _index(default_dir / "INDEX.md", warnings)
    try:
        personal = _personal_dir(config_root)
    except ValueError as error:
        warnings.append(str(error))
        personal = None
    if personal and ((personal / "INDEX.md").exists() or (personal / "INDEX.md").is_symlink()):
        for name in _index(personal / "INDEX.md", warnings):
            if name not in names:
                names.append(name)
    sections = []
    for name in names:
        override = personal / name if personal else None
        path = override if override and (override.exists() or override.is_symlink()) else default_dir / name
        try:
            sections.append(f"<!-- module: {name} -->\n{_read(path)}")
        except (OSError, ValueError) as error:
            warnings.append(f"Cannot read {path}: {error}")
    deferred_names = {p.name for p in default_dir.glob("*.md")}
    if personal:
        deferred_names.update(p.name for p in personal.glob("*.md"))
    deferred = []
    for name in sorted(deferred_names - set(names) - {"INDEX.md", "control-return.md"}):
        try:
            _module_name(name)
        except ValueError:
            continue
        override = personal / name if personal else None
        path = override if override and (override.exists() or override.is_symlink()) else default_dir / name
        try:
            _read(path)
            deferred.append(f"- {name}: {path.resolve()}")
        except (OSError, ValueError) as error:
            warnings.append(f"Cannot read {path}: {error}")
    if sections and deferred:
        sections.append("Deferred references (read only when an active module calls for it):\n" + "\n".join(deferred))
    if sections and warnings:
        sections.append("Not loaded (unreadable; do not claim these rules are applied):\n" +
                        "\n".join(f"- {warning}" for warning in warnings))
    return "\n\n".join(sections), warnings


def load_control_return(skill_md: Path, config_root: Path) -> tuple[str, list[str]]:
    """Use a complete personal rule or only the packaged Rule block."""
    try:
        override = _personal_dir(config_root) / "control-return.md"
        if override.exists() or override.is_symlink():
            return _read(override), []
        text = _read(skill_md)
        match = RULE_BLOCK.search(text)
        if not match or not match.group(1).strip():
            raise ValueError(f"No ```text block under '## Rule' in {skill_md}")
        return match.group(1).strip(), []
    except (OSError, ValueError) as error:
        return "", [f"control-return: {error}; rule was not loaded"]


def _atomic_write(path: Path, text: str) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".rule-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _metadata(path: Path) -> dict:
    value = json.loads(_read(path))
    if not isinstance(value, dict) or not isinstance(value.get("modules"), dict):
        raise ValueError("Invalid personal base-hash metadata")
    for name, record in value["modules"].items():
        _module_name(name)
        if not isinstance(record, dict) or "base_hash" not in record:
            raise ValueError(f"Invalid base-hash record: {name}")
        base = record["base_hash"]
        if base is not None and (not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{64}", base)):
            raise ValueError(f"Invalid base hash: {name}")
    return value


def save_module_override(config_root: Path, module: str, content: str,
                         base_hash: str | None, expected_hash: str | None) -> Path:
    """Save an explicitly confirmed edit; None expects no existing personal file."""
    if os.name != "posix":
        raise ValueError("Personal rule writes require POSIX locks (macOS, Linux or WSL)")
    import fcntl
    _module_name(module)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Rule content must be non-empty")
    for value in (base_hash, expected_hash):
        if value is not None and not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError("Expected a SHA-256 hash")
    personal = _personal_dir(config_root)
    personal.mkdir(parents=True, exist_ok=True)
    # Keep this inode: unlinking a lock permits two concurrent lock owners.
    fd = os.open(personal / ".write.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = personal / module
        if path.is_symlink():
            raise ValueError(f"Symlink rule is not allowed: {path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual != expected_hash:
            raise ValueError(f"Rule changed since preview: {module}; reload before confirming")
        metadata_path = personal / ".base-hashes.json"
        metadata = _metadata(metadata_path) if metadata_path.exists() else {"modules": {}}
        index_path = personal / "INDEX.md"
        index = None
        if base_hash is None and actual is None and module != "control-return.md":
            index = _read(index_path) + "\n" if index_path.exists() else "| Module | File | Purpose |\n| --- | --- | --- |\n"
            index += f"| {module[:-3]} | {module} | Personal module |\n"
        metadata["modules"].setdefault(module, {"base_hash": base_hash})
        _atomic_write(path, content)
        _atomic_write(metadata_path, json.dumps(metadata, indent=2) + "\n")
        if index is not None:
            _atomic_write(index_path, index)
        return path


def check_preference_updates(default_dir: Path, config_root: Path,
                             control_return_skill: Path | None = None) -> list[dict]:
    """Report package changes hidden by personal copies, without merging them."""
    try:
        personal = _personal_dir(config_root)
        path = personal / ".base-hashes.json"
        if not path.exists():
            return []
        metadata = _metadata(path)
        results = []
        for name, record in metadata["modules"].items():
            _module_name(name)
            base = record["base_hash"]
            if base is None or not (personal / name).is_file():
                continue
            if name == "control-return.md":
                if control_return_skill is None:
                    continue
                match = RULE_BLOCK.search(_read(control_return_skill))
                if not match:
                    raise ValueError(f"No Rule block in {control_return_skill}")
                actual = hashlib.sha256(match.group(1).strip().encode("utf-8")).hexdigest()
            else:
                default = default_dir / name
                actual = hashlib.sha256(default.read_bytes()).hexdigest() if default.is_file() else None
            if base != actual:
                results.append({"component": f"preferences:{name}", "status": "default_changed",
                                "message": "Packaged default changed; personal override was preserved"})
        return results
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [{"component": "preferences", "status": "invalid", "message": str(error)}]


def main(argv: list[str] | None = None) -> int:
    """CLI for effective reads and writes already approved in the calling skill workflow."""
    from .config import resolve_config_root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    load = commands.add_parser("load")
    load.add_argument("--default-dir", type=Path, required=True)
    save = commands.add_parser("save")
    save.add_argument("--module", required=True)
    save.add_argument("--content-file", type=Path, required=True)
    save.add_argument("--base-hash")
    save.add_argument("--expected-hash")
    args = parser.parse_args(argv)
    try:
        env = dict(os.environ)
        if args.config_root:
            env["AGENT_SKILLS_CONFIG_DIR"] = str(args.config_root)
        root = resolve_config_root(env, Path.home())
        if args.command == "load":
            content, warnings = load_preferences(args.default_dir, root)
            print(json.dumps({"content": content, "warnings": warnings}, ensure_ascii=False))
            return int(bool(warnings))
        path = save_module_override(root, args.module, args.content_file.read_text(encoding="utf-8"),
                                    args.base_hash, args.expected_hash)
        print(json.dumps({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

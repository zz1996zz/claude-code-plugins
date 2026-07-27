#!/usr/bin/env python3
"""Load, validate, initialize, and repair the per-user pl memory backend config."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKENDS = ("obsidian", "notion")

# A pl Obsidian vault is fingerprinted by INDEX.md plus these adapter-created directories.
VAULT_MARKERS = ("decisions", "features", "work")

# Never descend into these while scanning for vault candidates (hidden dirs are always skipped).
SKIP_DIRS = frozenset(
    {"node_modules", "Library", "Applications", "Movies", "Music", "Pictures", "venv", "__pycache__"}
)


def validate(data: dict) -> dict:
    backend = data.get("backend")
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of {BACKENDS}: got {backend!r}")
    if backend == "obsidian":
        root = (data.get("obsidian") or {}).get("root")
        if not root or not str(root).strip():
            raise ValueError("obsidian.root is required for the obsidian backend")
        data["obsidian"]["root"] = str(Path(str(root)).expanduser())
        if not Path(data["obsidian"]["root"]).is_absolute():
            raise ValueError("obsidian.root must be an absolute path")
    else:
        page = (data.get("notion") or {}).get("rootPage")
        if not page or not str(page).strip():
            raise ValueError("notion.rootPage is required for the notion backend")
    return data


def load(config_path: Path) -> dict:
    if not config_path.is_file():
        raise FileNotFoundError(f"config not found: {config_path}")
    return validate(json.loads(config_path.read_text(encoding="utf-8")))


def cmd_show(args: argparse.Namespace) -> int:
    print(json.dumps(load(Path(args.config).expanduser()), ensure_ascii=False, indent=2))
    return 0


def find_vault_candidates(search_root: Path, max_depth: int = 4) -> list[dict]:
    """Find directories that look like a pl Obsidian vault (INDEX.md + marker dirs)."""
    root = search_root.expanduser()
    candidates: list[dict] = []
    if not root.is_dir():
        return candidates
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        path = Path(dirpath)
        if len(path.parts) - base_depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS]
        if "INDEX.md" in filenames and all((path / m).is_dir() for m in VAULT_MARKERS):
            candidates.append(
                {
                    "root": str(path),
                    "markers": ["INDEX.md", *VAULT_MARKERS],
                    "notes": sum(1 for _ in path.rglob("*.md")),
                }
            )
            dirnames[:] = []  # a vault never nests another vault; stop descending
    return candidates


def cmd_repair(args: argparse.Namespace) -> int:
    """Report config health; when missing, detect existing vaults instead of forcing re-onboarding.

    Never writes anything: the orchestrator confirms a candidate with the user, then re-links
    via `init --backend obsidian --obsidian-root <root>`. Exit 0 = config OK or candidates
    found; exit 1 = config missing and nothing detected (full onboarding required).
    """
    try:
        data = load(Path(args.config).expanduser())
    except (FileNotFoundError, ValueError, json.JSONDecodeError, AttributeError, TypeError):
        data = None
    if data is not None:
        print(json.dumps({"status": "ok", "config": data}, ensure_ascii=False, indent=2))
        return 0
    candidates = find_vault_candidates(Path(args.search_root), args.max_depth)
    print(
        json.dumps(
            {
                "status": "missing",
                "candidates": candidates,
                "note": (
                    "repair detects Obsidian vaults only; a Notion backend cannot be detected "
                    "from disk. Confirm a candidate with the user, then re-link with: "
                    "init --backend obsidian --obsidian-root <root>"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if candidates else 1


def cmd_init(args: argparse.Namespace) -> int:
    data: dict = {"backend": args.backend}
    if args.backend == "obsidian":
        data["obsidian"] = {
            "root": str(Path(args.obsidian_root).expanduser().resolve()) if args.obsidian_root else ""
        }
    else:
        data["notion"] = {"rootPage": args.notion_root_page or ""}
    validate(data)
    path = Path(args.config).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show")
    show.set_defaults(func=cmd_show)
    init = sub.add_parser("init")
    init.add_argument("--backend", required=True, choices=BACKENDS)
    init.add_argument("--obsidian-root")
    init.add_argument("--notion-root-page")
    init.set_defaults(func=cmd_init)
    repair = sub.add_parser("repair", help="detect an existing vault when the config is missing")
    repair.add_argument("--search-root", default="~")
    repair.add_argument("--max-depth", type=int, default=4)
    repair.set_defaults(func=cmd_repair)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

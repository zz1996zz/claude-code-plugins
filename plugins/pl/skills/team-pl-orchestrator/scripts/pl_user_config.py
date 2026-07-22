#!/usr/bin/env python3
"""Load, validate, and initialize the per-user pl memory backend config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKENDS = ("obsidian", "notion")


def validate(data: dict) -> dict:
    backend = data.get("backend")
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of {BACKENDS}: got {backend!r}")
    if backend == "obsidian":
        root = (data.get("obsidian") or {}).get("root")
        if not root or not str(root).strip():
            raise ValueError("obsidian.root is required for the obsidian backend")
        data["obsidian"]["root"] = str(Path(str(root)).expanduser())
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


def cmd_init(args: argparse.Namespace) -> int:
    data: dict = {"backend": args.backend}
    if args.backend == "obsidian":
        data["obsidian"] = {"root": args.obsidian_root or ""}
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

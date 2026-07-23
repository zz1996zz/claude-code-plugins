#!/usr/bin/env python3
"""Tests for the per-user memory backend config helper."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "pl_user_config.py"


class PlUserConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / "data" / "config.json"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(SCRIPT), "--config", str(self.config), *args],
            capture_output=True,
            text=True,
        )

    def test_init_obsidian_then_show_round_trip(self) -> None:
        result = self.run_cli("init", "--backend", "obsidian", "--obsidian-root", "~/vault")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.config.is_file())

        shown = self.run_cli("show")
        self.assertEqual(0, shown.returncode, shown.stderr)
        data = json.loads(shown.stdout)
        self.assertEqual("obsidian", data["backend"])
        self.assertNotIn("~", data["obsidian"]["root"])  # expanduser 적용

    def test_init_notion_stores_root_page(self) -> None:
        url = "https://www.notion.so/team/PL-Memory-abc123"
        result = self.run_cli("init", "--backend", "notion", "--notion-root-page", url)
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual({"backend": "notion", "notion": {"rootPage": url}}, data)

    def test_show_without_config_fails(self) -> None:
        result = self.run_cli("show")
        self.assertEqual(2, result.returncode)
        self.assertIn("config not found", result.stderr)

    def test_invalid_backend_rejected(self) -> None:
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(json.dumps({"backend": "dropbox"}), encoding="utf-8")
        result = self.run_cli("show")
        self.assertEqual(2, result.returncode)
        self.assertIn("backend must be one of", result.stderr)

    def test_init_obsidian_without_root_rejected(self) -> None:
        result = self.run_cli("init", "--backend", "obsidian")
        self.assertEqual(2, result.returncode)
        self.assertIn("obsidian.root is required", result.stderr)

    def test_init_resolves_relative_root_to_absolute(self) -> None:
        result = self.run_cli("init", "--backend", "obsidian", "--obsidian-root", "vault")
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertTrue(data["obsidian"]["root"].startswith("/"))

    def test_show_rejects_relative_root_in_config(self) -> None:
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(
            json.dumps({"backend": "obsidian", "obsidian": {"root": "vault"}}),
            encoding="utf-8",
        )
        result = self.run_cli("show")
        self.assertEqual(2, result.returncode)
        self.assertIn("absolute", result.stderr)

    def test_malformed_config_shape_exits_cleanly(self) -> None:
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(
            json.dumps({"backend": "obsidian", "obsidian": "vault"}), encoding="utf-8"
        )
        result = self.run_cli("show")
        self.assertEqual(2, result.returncode)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

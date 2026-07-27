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

    def _make_vault(self, relative: str) -> Path:
        vault = Path(self.tmp.name) / relative
        for marker in ("decisions", "features", "work"):
            (vault / marker).mkdir(parents=True)
        (vault / "INDEX.md").write_text("# index\n", encoding="utf-8")
        (vault / "decisions" / "sample.md").write_text("x\n", encoding="utf-8")
        return vault

    def test_repair_with_valid_config_reports_ok(self) -> None:
        vault = self._make_vault("vault")
        self.run_cli("init", "--backend", "obsidian", "--obsidian-root", str(vault))
        result = self.run_cli("repair", "--search-root", self.tmp.name)
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual("ok", data["status"])
        self.assertEqual("obsidian", data["config"]["backend"])

    def test_repair_missing_config_finds_vault_and_writes_nothing(self) -> None:
        vault = self._make_vault("notes/memory")
        result = self.run_cli("repair", "--search-root", self.tmp.name)
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual("missing", data["status"])
        self.assertEqual([str(vault)], [c["root"] for c in data["candidates"]])
        self.assertEqual(2, data["candidates"][0]["notes"])  # INDEX.md + sample.md
        self.assertFalse(self.config.exists())  # repair는 절대 쓰지 않는다

    def test_repair_missing_config_no_candidates_exits_1(self) -> None:
        result = self.run_cli("repair", "--search-root", self.tmp.name)
        self.assertEqual(1, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual("missing", data["status"])
        self.assertEqual([], data["candidates"])

    def test_repair_ignores_partial_vault_markers(self) -> None:
        partial = Path(self.tmp.name) / "half"
        (partial / "decisions").mkdir(parents=True)
        (partial / "INDEX.md").write_text("# index\n", encoding="utf-8")  # features/work 없음
        result = self.run_cli("repair", "--search-root", self.tmp.name)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual([], json.loads(result.stdout)["candidates"])

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

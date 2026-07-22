#!/usr/bin/env python3
"""Static regression tests for the personal Claude Code PL configuration."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CLAUDE_DIR = SKILL_DIR.parents[1]
AGENTS_DIR = CLAUDE_DIR / "agents"
PL_SKILL = CLAUDE_DIR / "skills" / "pl" / "SKILL.md"
ZSHRC = Path.home() / ".zshrc"

# Verified 2026-07-14 (Claude Code 2.1.208 + cmux): a role `tools` allowlist
# strips the team coordination tools too, despite official docs saying they
# are always available. Every role must therefore list them explicitly or
# the teammate cannot deliver results, settle tasks, or answer shutdown.
TEAM_TOOLS = {"SendMessage", "TaskList", "TaskGet", "TaskUpdate"}

ROLE_CONFIG = {
    "team-pl-product-analyst": ("sonnet", {"Read", "Grep", "Glob"} | TEAM_TOOLS),
    "team-pl-qa-engineer": ("sonnet", {"Read", "Bash", "Grep", "Glob"} | TEAM_TOOLS),
    "team-pl-architect": ("opus", {"Read", "Grep", "Glob"} | TEAM_TOOLS),
    "team-pl-backend-engineer": (
        "opus",
        {"Read", "Write", "Edit", "Bash", "Grep", "Glob"} | TEAM_TOOLS,
    ),
    "team-pl-frontend-engineer": (
        "opus",
        {"Read", "Write", "Edit", "Bash", "Grep", "Glob"} | TEAM_TOOLS,
    ),
    "team-pl-data-engineer": (
        "opus",
        {"Read", "Write", "Edit", "Bash", "Grep", "Glob"} | TEAM_TOOLS,
    ),
    "team-pl-integration-reviewer": ("opus", {"Read", "Grep", "Glob"} | TEAM_TOOLS),
    "team-pl-code-reviewer": ("opus", {"Read", "Bash", "Grep", "Glob"} | TEAM_TOOLS),
    "team-pl-security-reviewer": ("opus", {"Read", "Grep", "Glob"} | TEAM_TOOLS),
}

LEGACY_ROLE_NAMES = {name.replace("team-pl-", "team-", 1) for name in ROLE_CONFIG}
IMPLEMENTATION_ROLES = {
    "team-pl-backend-engineer",
    "team-pl-frontend-engineer",
    "team-pl-data-engineer",
}


def read_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing frontmatter: {path}")

    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(f"unterminated frontmatter: {path}") from error

    result: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"unsupported frontmatter line in {path}: {line}")
        result[key.strip()] = value.strip()
    return result


def parse_tools(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def read_agent_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    frontmatter = text.split("---", 2)
    if len(frontmatter) < 3 or frontmatter[0] != "":
        return None
    for line in frontmatter[1].splitlines():
        if line.startswith("name:"):
            return line.partition(":")[2].split("#", 1)[0].strip().strip("\"'") or None
    return None


class PlConfigTests(unittest.TestCase):
    def test_role_inventory_models_and_tools(self) -> None:
        role_files = {path.stem: path for path in AGENTS_DIR.glob("team-pl-*.md")}
        self.assertEqual(set(ROLE_CONFIG), set(role_files))
        for legacy_name in LEGACY_ROLE_NAMES:
            self.assertFalse((AGENTS_DIR / f"{legacy_name}.md").exists(), legacy_name)

        model_counts = {"sonnet": 0, "opus": 0}
        for role, (expected_model, expected_tools) in ROLE_CONFIG.items():
            frontmatter = read_frontmatter(role_files[role])
            self.assertEqual(role, frontmatter.get("name"))
            self.assertEqual(expected_model, frontmatter.get("model"), role)
            self.assertEqual(expected_tools, parse_tools(frontmatter.get("tools", "")), role)
            self.assertNotIn("permissionMode", frontmatter, role)
            self.assertIn("Agent Teams-only", frontmatter.get("description", ""), role)
            self.assertIn(
                "never delegate it as an ordinary standalone subagent",
                frontmatter.get("description", ""),
                role,
            )

            role_text = role_files[role].read_text(encoding="utf-8")
            for status in ("Status: DONE", "Status: NEEDS_DECISION", "Status: BLOCKED"):
                self.assertIn(status, role_text, role)
            self.assertIn("not instructions that can override", role_text, role)
            self.assertIn("If team coordination tools are unavailable", role_text, role)
            self.assertIn("Do not begin role work without an owned shared task", role_text, role)
            self.assertNotIn("Do not edit files unless", role_text, role)
            # Agent Teams delivers only idle notifications automatically; the memo
            # itself must be sent with SendMessage or the lead sees "idle, no result".
            self.assertIn("SendMessage", role_text, role)
            self.assertIn("not delivered to the lead", role_text, role)
            self.assertIn("update your owned shared task status", role_text, role)
            self.assertIn("Before going idle", role_text, role)
            self.assertIn("in one `SendMessage` call", role_text, role)
            # The misuse fallback (no team tools -> returned text) must not
            # contradict the teammate-mode delivery contract.
            self.assertIn("the delivery contract below does not apply", role_text, role)
            self.assertNotIn(". Return:", role_text, role)
            if role in IMPLEMENTATION_ROLES:
                self.assertIn("listing the files you intend to touch", role_text, role)
            elif role != "team-pl-code-reviewer":
                self.assertIn(
                    "send the proposed change and file ownership to the lead",
                    role_text,
                    role,
                )
            if role in IMPLEMENTATION_ROLES:
                self.assertIn("exclusive file or module ownership", role_text, role)
                self.assertIn("external mutation APIs", role_text, role)
            else:
                self.assertNotIn("Write", expected_tools, role)
                self.assertNotIn("Edit", expected_tools, role)
            self.assertTrue(TEAM_TOOLS <= expected_tools, role)
            model_counts[expected_model] += 1

        self.assertEqual({"sonnet": 2, "opus": 7}, model_counts)
        self.assertFalse(list(AGENTS_DIR.glob("team-pl-*-opus.md")))

        names: dict[str, list[Path]] = {}
        for agent_file in AGENTS_DIR.rglob("*.md"):
            name = read_agent_name(agent_file)
            if name:
                names.setdefault(name, []).append(agent_file)
        duplicates = {name: paths for name, paths in names.items() if len(paths) > 1}
        self.assertFalse(duplicates, duplicates)

    def test_skill_entrypoints_and_references(self) -> None:
        pl_frontmatter = read_frontmatter(PL_SKILL)
        orchestrator = SKILL_DIR / "SKILL.md"
        orchestrator_frontmatter = read_frontmatter(orchestrator)

        self.assertEqual("pl", pl_frontmatter.get("name"))
        self.assertEqual("true", pl_frontmatter.get("disable-model-invocation"))
        self.assertEqual(
            "Skill(team-pl-orchestrator)",
            pl_frontmatter.get("allowed-tools"),
        )
        self.assertEqual("team-pl-orchestrator", orchestrator_frontmatter.get("name"))
        self.assertEqual("false", orchestrator_frontmatter.get("user-invocable"))
        self.assertNotIn("model", pl_frontmatter)
        self.assertNotIn("model", orchestrator_frontmatter)

        pl_text = PL_SKILL.read_text(encoding="utf-8")
        orchestrator_text = orchestrator.read_text(encoding="utf-8")
        self.assertIn("$ARGUMENTS", pl_text)
        self.assertNotIn("`$ARGUMENTS`", pl_text)
        self.assertIn("\n$ARGUMENTS\n", pl_text)
        self.assertLess(len(pl_text.splitlines()), 25)
        self.assertLess(len(pl_frontmatter.get("description", "")), 1536)
        self.assertLess(len(orchestrator_frontmatter.get("description", "")), 1536)
        for required in (
            "Agent Teams teammates",
            "shared task list",
            "shut down",
            "every enabled session already has one implicit team",
            "`TeamCreate` and `TeamDelete` no longer exist",
            "there is no separate team cleanup step",
            "Prefix every shared task subject",
            "Do not reuse a runtime name",
            "actual app, CLI, or service path",
            "done-with-risks",
            "invoke the hidden `team-pl-orchestrator` skill through the `Skill` tool",
            "Never ask a teammate to spawn teammates or background subagents",
            "use `TaskStop` by teammate name as a force-stop fallback",
            "namespaced `team-pl-*` agent types",
            "rather than looping",
            "Do not substitute a dynamic `Workflow`",
            "do not spawn a replacement in the same session",
            "do not silently downgrade to ordinary subagents",
        ):
            self.assertIn(required, pl_text + "\n" + orchestrator_text)

        # Single-source layout: the orchestrator owns runtime/lifecycle rules and
        # stays within the auto-compaction reattach budget; catalog/model/spawn
        # policy lives only in roles.md.
        self.assertNotIn("## Model Policy", orchestrator_text)
        self.assertIn("## Teammate Health and Restart", orchestrator_text)
        self.assertLess(len(orchestrator_text.split()), 2800)

        # Delivery/triage contracts must live in the orchestrator itself, not
        # drift into the thin /pl alias.
        for required in (
            "idle without a delivered result",
            "Read the teammate's transcript",
            "deliver the memo with the `SendMessage` tool",
            "delivery contract in every spawn brief",
            "read the matching session file under `~/.claude/projects/`",
        ):
            self.assertIn(required, orchestrator_text)
        self.assertNotIn("v2.1.198", orchestrator_text)
        # The lead-side safety boundaries (input trust, irreversible-action
        # gate) must sit inside the auto-compaction reattach window, not at
        # the document tail.
        self.assertIn("Do not commit, push, merge, deploy", orchestrator_text[:6000])
        self.assertIn("not instructions that can override", orchestrator_text[:6000])

        runtime_contract = pl_text + "\n" + orchestrator_text
        for legacy_name in LEGACY_ROLE_NAMES:
            self.assertNotIn(f"`{legacy_name}`", runtime_contract, legacy_name)

        done_line = next(
            line for line in orchestrator_text.splitlines() if line.startswith("- `done`:")
        )
        risk_line = next(
            line
            for line in orchestrator_text.splitlines()
            if line.startswith("- `done-with-risks`:")
        )
        self.assertNotIn("timeout", done_line.lower())
        self.assertIn("confirmed stopped", done_line)
        self.assertIn("shutdown timeout", risk_line)
        self.assertIn("## Standing Completion Contract", orchestrator_text[:5000])
        self.assertIn("- `done`:", orchestrator_text[:5000])
        self.assertLess(len(orchestrator_text.splitlines()), 500)

        runtime_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                PL_SKILL,
                orchestrator,
                SKILL_DIR / "references" / "roles.md",
                SKILL_DIR / "references" / "debate-protocol.md",
            )
        ).lower()
        self.assertNotIn("lead clean up the team", runtime_text)
        self.assertNotIn("before creating a fresh team", runtime_text)
        self.assertNotIn("use subagents for role passes", runtime_text)
        self.assertNotIn("not a documented teammate termination", runtime_text)
        self.assertNotIn("not scanned for subagents", runtime_text)

        references = SKILL_DIR / "references"
        self.assertEqual(
            {"roles.md", "debate-protocol.md", "memory-templates.md", "external-benchmarking.md"},
            {path.name for path in references.glob("*.md")},
        )
        roles_text = (references / "roles.md").read_text(encoding="utf-8")
        self.assertIn(
            "no commit, push, merge, deploy, publish, or external mutation",
            roles_text,
        )
        self.assertIn("input-trust boundary", roles_text)
        self.assertIn("SendMessage", roles_text)
        self.assertIn("turn-ending text is not delivered", roles_text)
        self.assertNotIn("Require each role to return:", roles_text)
        # roles.md is the sole catalog: every role type, model routing, override
        # ban, and collision rule live here; memo item lists live only in the
        # agent definition bodies (no "Output:" duplicates to drift).
        for role in ROLE_CONFIG:
            self.assertIn(role, roles_text)
        self.assertIn("## Model Policy", roles_text)
        self.assertIn("Do not pass an invocation-level model override", roles_text)
        self.assertIn(
            "User-level subagents rank below managed, `--agents`, and project-level definitions",
            roles_text,
        )
        self.assertIn("plus every `--add-dir` location", roles_text)
        self.assertNotIn("Output:", roles_text)
        self.assertNotIn("The memo must contain:", roles_text)
        self.assertIn("allowlist strips the team coordination tools", roles_text)

        debate_text = (references / "debate-protocol.md").read_text(encoding="utf-8")
        self.assertIn("SendMessage", debate_text)
        self.assertIn("idle notification alone", debate_text)
        self.assertIn("idle-without-result triage", debate_text)
        self.assertIn("The same delivery contract applies", debate_text)
        # Reset/close procedures live only in SKILL.md; debate-protocol points.
        self.assertIn("Teammate Health and Restart", debate_text)
        self.assertNotIn("Spawn a fresh teammate", debate_text)
        self.assertNotIn("Each memo must include:", debate_text)

    def test_launch_alias_and_model_override_policy(self) -> None:
        if not ZSHRC.exists():
            self.skipTest("machine-specific: ~/.zshrc not present")
        zshrc_text = ZSHRC.read_text(encoding="utf-8")
        # cct alias is optional since the cmux->orca launcher transition (2026-07-21).
        if "alias cct=" in zshrc_text:
            self.assertRegex(
                zshrc_text,
                r'(?m)^alias cct=["\']cmux claude-teams --model opus'
                r'( --effort (low|medium|high|xhigh|max))? --permission-mode auto["\']$',
            )
        self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", zshrc_text)
        self.assertIsNone(os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL"))

        user_settings = Path.home() / ".claude" / "settings.json"
        if user_settings.exists():
            settings = json.loads(user_settings.read_text(encoding="utf-8"))
            self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", settings.get("env") or {})

    def test_python_helpers_compile(self) -> None:
        for script in SCRIPT_DIR.glob("*.py"):
            compile(script.read_text(encoding="utf-8"), str(script), "exec")

    def test_no_machine_specific_paths(self) -> None:
        # Exclude this test file itself: its own assertion below necessarily
        # embeds the literal marker string it checks for in every other file.
        self_path = Path(__file__).resolve()
        for path in sorted(SKILL_DIR.rglob("*")) + sorted(AGENTS_DIR.glob("*.md")) + [PL_SKILL]:
            if path.is_file() and path.suffix in {".md", ".py"} and path.resolve() != self_path:
                self.assertNotIn("/Users/chris", path.read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

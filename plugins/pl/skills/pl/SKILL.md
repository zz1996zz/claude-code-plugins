---
name: pl
description: Short alias for the team PL orchestrator. Use when the user invokes /pl or asks a PL/tech-lead agent to run feature work. For non-trivial feature work, explicitly spawn Claude Code Agent Teams teammates, not ordinary subagents, before implementation; run role-agent discussion, make decisions, implement, test, and update the user-selected memory backend (Obsidian vault or Notion).
argument-hint: "[feature request]"
disable-model-invocation: true
allowed-tools: Skill(pl:team-pl-orchestrator)
---

# PL

Before any workflow action, invoke the hidden `pl:team-pl-orchestrator` skill through the `Skill` tool and follow it. This keeps the orchestrator instructions in the skill lifecycle across turns and auto-compaction.

Treat explicit `/pl` invocation as explicit permission to use the team PL orchestration workflow for the current request, including role-agent discussion, implementation, verification, and memory backend updates.

## Request

$ARGUMENTS

For non-trivial feature work, do not begin implementation until the orchestrator has inspected current tasks and explicitly spawned the required Claude Code Agent Teams teammates using the namespaced `team-pl-*` agent types. If the `Skill` tool or hidden skill is unavailable, read ${CLAUDE_PLUGIN_ROOT}/skills/team-pl-orchestrator/SKILL.md directly and follow it as the fallback source of truth.

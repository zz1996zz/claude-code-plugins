# Memory Templates

Use these templates in the configured memory backend (see the adapter references).

## Contents

- Note Format
- Workspace Layout
- Helper Script
- Feature Note
- Decision Note

## Note Format

Feature and decision notes start with YAML frontmatter (OKF-compatible: `type`, `title`, `status`, `date`, `owner`, `work`, plus `repo`/`status_note`/`tags` when relevant). Frontmatter is the single machine-read surface: Obsidian indexes it natively (property search, Bases/Dataview) and agents can read only the first lines of a file to know its state without parsing the body. Relational links (`Related decisions:`, `Related feature:`, etc.) stay in the body under the H1 so link validation and backlink insertion keep working. Do not duplicate frontmatter fields as plain body lines; legacy unmigrated notes with a plain `Status:` line are still accepted by `check` as a fallback only.

## Workspace Layout

Store new work under a 업무/project namespace:

```text
<vault-root>/
  INDEX.md
  work/
    <work-slug>/
      INDEX.md
      features/
        YYYY-MM-DD-feature-slug.md
      decisions/
        YYYY-MM-DD-decision-slug.md
      architecture/
        README.md
```

Selection rule:
- If the user names a 업무/project/product, slugify that name.
- Otherwise use the current repository name.
- If neither is clear, use `inbox` only as a temporary namespace and record why.

Never put unrelated 업무 A and 업무 B in the same feature note or decision folder.

Use relative Markdown links between feature and decision notes. The feature note links to every durable decision, and each decision links back to its feature. Keep superseded notes; mark their status and successor instead of deleting history.

## Helper Script

Prefer the bundled helper for new notes and index maintenance:

```bash
python3 <skill-dir>/scripts/memory_note.py init-work <work-slug> --repo <repo-path>
python3 <skill-dir>/scripts/memory_note.py feature <work-slug> "<feature title>" --repo <repo-path>
python3 <skill-dir>/scripts/memory_note.py decision <work-slug> "<decision title>" --feature features/<feature-file>.md
python3 <skill-dir>/scripts/memory_note.py check
```

Use `${CLAUDE_PLUGIN_ROOT}/skills/team-pl-orchestrator` as `<skill-dir>` when the current skill directory is unclear.
The `check` command synchronizes workspace indexes, handles both section-based legacy indexes and the current `Features:`/`Decisions:` layout without duplicate entries, validates local Markdown links, and enforces the feature-note frontmatter `status:` vocabulary (`in-progress`, `done`, `done-with-risks`, `blocked`; the creator rejects other values too; a plain body `Status:` line is read only as a legacy fallback). Free-text detail goes in the body or a frontmatter `status_note:` field.
The helper rejects invalid dates, multiline/control-character metadata, symlinked work namespaces, feature paths outside the selected work namespace, and same-date slug collisions between different titles. Markdown link labels are escaped when indexes and backlinks are generated.
After changing the helper, run `python3 <skill-dir>/scripts/test_memory_note.py` before using it on the real vault.

## Feature Note

Path: `work/<work-slug>/features/YYYY-MM-DD-feature-slug.md`

```markdown
---
type: Feature
title: "<name>"
status: in-progress
date: <YYYY-MM-DD>
owner: PL agent
work: <work-slug>
repo: "<path or repo name>"
---

# Feature: <name>

Related decisions:
Related PR/commit:

## Request

<user request>

## Scope

In:
- 

Out:
- 

## Relevant Memory

- 

## Roles

- product-analyst:
- architect:
- qa-engineer:
- code-reviewer:
- selected conditional roles:

## Team Lifecycle

- Spawned:
- Reused:
- Replaced:
- Shut down:
- Force-stopped:
- Unconfirmed stop:
- Runtime cleanup: automatic on Claude session exit / not applicable

## Discussion Summary

### Round 1

### Synthesis

### Round 2

### Direct Challenges

- <challenger> -> <recipient>: <claim, response, effect on decision>

## PL Decisions

- 

## Implementation Plan

1. 

## Execution Ledger

| Task | Owner | Depends on | Deliverable | Status | Evidence |
|---|---|---|---|---|---|
| T1 |  |  |  | pending |  |

## Implementation Summary

- 

## Changed Files

- 

## Verification

- Command:
- Result:
- Fresh after final code change: yes/no
- Notes:

## Completion

- Status: in-progress / done / done-with-risks / blocked
- Residual risk:

## Open Questions

- 
```

## Decision Note

Path: `work/<work-slug>/decisions/YYYY-MM-DD-decision-slug.md`

```markdown
---
type: Decision
title: "<name>"
status: accepted
date: <YYYY-MM-DD>
owner: PL agent
work: <work-slug>
---

# Decision: <name>

Related feature:
Related files:
Related sources:
Supersedes:
Superseded by:

## Context

<why this decision was needed>

## Options Considered

1. 
2. 
3. 

## Decision

<selected option>

## Rationale

<evidence and reasoning summary>

## Consequences

Positive:
- 

Negative:
- 

## Validation

- 

## Open Questions

- 
```

# Debate Protocol

Use this protocol to create productive role-agent discussion without uncontrolled chatter.

## Contents

- Round 0: Brief
- Round 1: Independent Role Memos
- Synthesis
- Round 2: Critique
- Teammate Reset
- Decision
- Implementation
- Review Loop
- Close
- Memory Hygiene

## Round 0: Brief

Create a shared brief:
- User request
- Relevant memory
- Current repo facts
- Constraints
- Proposed role roster
- Predictable teammate runtime names
- Expected deliverables
- Acceptance criteria and evidence required

Create one shared task per independent memo. Each task must state:
- A subject prefixed with `[<feature-slug>]`
- Task ID and owner
- Dependencies
- Bounded deliverable
- Success criteria
- Files the teammate may edit, or `read-only`
- The verification command that decides completion (`Run: <command>`), when the task has a runnable check

## Round 1: Independent Role Memos

Ask each selected role to respond independently. Do not show other role outputs during Round 1 unless the platform provides true agent-team communication and direct debate is useful.

Each memo leads with its `Status:` line and covers the deliverable items defined in the role's definition body.

Each teammate delivers the memo to the lead with `SendMessage` and updates its shared task before going idle. Never treat an idle notification alone as a delivered memo: if a teammate goes idle without one, run the idle-without-result triage in `SKILL.md` (task state, transcript, one explicit `SendMessage` nudge) before any reset.

## Synthesis

The PL lead summarizes:
- Agreements
- Conflicts
- Hidden assumptions
- Decisions required
- Proposed implementation plan
- Proposed verification plan

## Round 2: Critique

Use direct teammate messages for material critique instead of sending every message to everyone. Assign each selected role one relevant peer claim to challenge, then have the recipient answer the challenge. Ask for:
- What is wrong or missing?
- Which decision is risky?
- Which simpler option should be considered?
- What must be tested?

Each challenge must name the claim, cite repo or requirement evidence, and state what would change the recommendation. Each response must accept, reject, or narrow the claim with evidence. Both teammates then send the PL a concise revised conclusion. The same delivery contract applies in every round: challenge answers and revised conclusions reach the PL only through `SendMessage`, and an idle teammate without a delivered response gets the same idle-without-result triage.

Run more rounds only when there is a material unresolved conflict. Stop when the PL can state the selected option, rejected alternatives, risks, and validation plan without relying on unresolved assumptions.

## Teammate Reset

Use reset instead of repeated prompting when a teammate gives stale, irrelevant, wrong-role, wrong-model, or obviously low-quality output. Reset targets bad output, not merely undelivered output; for an idle teammate with no delivered memo, complete the idle-without-result triage in `SKILL.md` first.

Before any reset, save useful facts from the teammate's output into the PL synthesis, and settle or reassign its shared task without marking abandoned work complete. Then follow the replacement procedure in `SKILL.md` under Teammate Health and Restart. Use at most one repair prompt before reset. Do not let one confused teammate dominate the discussion.

## Decision

The PL lead decides. Do not average opinions. Choose the option that best fits:
- User goal
- Existing repo patterns
- Maintainability
- Risk
- Testability
- Reversibility

Record durable decisions in memory.

Before any edit, run an analyze gate: check that the decisions, the implementation plan, and the shared tasks are consistent — every decision maps to at least one task, every task traces back to the plan, and no accepted decision or required deliverable is missing a task. Resolve mismatches before delegating work; a gap here surfaces later as unowned or contradictory implementation.

Before delegated implementation, convert the decision into dependency-aware shared tasks. Assign one owner per task and one owner per file. For complex or risky edits, require plan approval before the implementation teammate can edit.

## Implementation

Prefer one final integrator. Agent Teams teammates share the working directory, so avoid having multiple agents edit the same files. Delegate implementation edits only when the lead can isolate ownership by file or module. Use separate worktrees only when the PL explicitly provisions and coordinates them.

Run only unblocked tasks in parallel. At every interface handoff, the producing teammate directly messages the consumer with the exact contract and evidence. Update the feature-note execution ledger after each completed wave so work can resume safely after compaction.

Do not coordinate role work through panes or ad hoc messages alone: every active teammate must own a visible shared task. After the lead accepts a teammate's final deliverable and no revision, dependency, or re-review remains, ask that teammate to shut down instead of retaining an idle pane.

## Review Loop

After implementation:
1. Summarize the diff.
2. Spawn code-reviewer on the final diff and accepted requirements; do not keep it idle before a diff exists. Brief it with scoped context only — accepted requirements and PL decisions, the `BASE_SHA..HEAD_SHA` range, and the diff summary — and never the lead's session history or reasoning trace, so the review judges the artifact, not the process.
3. Require two ordered review gates, both of which must pass:
   - Gate 1 — spec/decision compliance: the diff satisfies the accepted requirements and PL decisions, with no silent scope drift.
   - Gate 2 — code quality: correctness, maintainability, behavior changes, and missing tests.
   A clean Gate 2 pass does not accept work that fails Gate 1. Rank findings by severity: fix Critical before any progress, Important before closing, and record Minor.
4. Ask QA to verify test coverage.
5. Ask data-engineer, integration-reviewer, or security-reviewer when the changed surface touches those areas.
6. Validate reviewer findings against the repo, fix material issues, rerun relevant tests, and re-review changed risk surfaces.

## Close

Close the feature under `SKILL.md`: confirm no required task is pending or merely stale, read fresh verification output instead of trusting teammate completion claims, bring feature and decision notes up to date, then follow the completion-or-cancellation checklist in `SKILL.md` Team Lifecycle (shutdown, force-stop confirmation, lifecycle evidence) and run the memory link/index check. Classify the result under the Standing Completion Contract.

## Memory Hygiene

Write summaries, not transcripts. Do not store secrets, credentials, or raw command logs. Durable notes should help a future LLM answer:
- What did we decide?
- Why?
- What alternatives were considered?
- What changed?
- How was it validated?
- What remains uncertain?

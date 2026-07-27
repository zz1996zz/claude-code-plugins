# Team Lifecycle and Teammate Health

Runtime rules for auditing, reusing, shutting down, and replacing Agent Teams teammates in PL-led feature work. Read this at the start of every `/pl` request before spawning anyone, when a teammate goes idle without a delivered result or misbehaves, and at completion or cancellation. Spawn policy (roles, models, timing, batching) lives in `roles.md`; the discussion loop lives in `debate-protocol.md`.

## Team Lifecycle

At the start of every `/pl` request:

1. Inspect active teammates and the shared task list before spawning anyone.
2. Reuse a healthy teammate only for a continuation of the same feature when its role and context still match.
3. For a new feature, settle the previous tasks, ask every old teammate to shut down, and confirm graceful or forced stop before spawning fresh role sessions in the same session-scoped implicit team. Verify genuinely completed tasks; delete obsolete pending tasks with task controls and record the abandonment in the old feature note. Never mark abandoned work completed. If an old stop cannot be confirmed, do not spawn a replacement in the same session: use a new Claude session for hard isolation or continue lead-only with the overlap risk recorded. Do not carry stale conclusions across feature boundaries.
4. Prefix every shared task subject with `[<feature-slug>]`. Task files can outlive teammate processes and session team config, so the prefix keeps sequential feature ledgers distinguishable.
5. Do not reuse a runtime name that already appeared in the current session. Use the next suffix such as `pl-architect-r2` for both replacements and later features.
6. After `/resume` or `/rewind`, reconcile the persisted task list but assume in-process teammates are gone until the panel proves otherwise; spawn replacements instead of messaging missing sessions.
7. Never edit `~/.claude/teams/` or `~/.claude/tasks/` by hand. Use teammate and task controls; Claude Code owns runtime config and retention.

During work:

1. Use direct messages for peer questions, challenge, and interface handoffs. Avoid broadcast unless every teammate is affected.
2. Wait for prerequisite analysis or implementation tasks before starting dependent work.
3. Monitor stuck or stale task states; verify the output, then correct task status or replace the teammate when necessary.
4. Require plan approval before a teammate edits for complex or risky implementation work.
5. Keep the shared task list authoritative. Do not let a teammate start role work without an owned task; reconstruct missing task entries before continuing.
6. After a teammate's final deliverable is accepted, shut it down when no dependency, revision, or re-review remains. Keep an idle teammate only for a named follow-up within the same feature.
7. A teammate row hidden after an idle timeout is still running and addressable. Do not treat a hidden pane or row as shutdown; confirm through the task/panel state or a named message.

At completion or cancellation:

1. Confirm no required task remains pending or in progress.
2. Collect concise outputs and update the feature note.
3. Ask every remaining teammate to shut down by runtime name. If a teammate rejects because work is active, resolve the task or delete it as obsolete and record the abandonment, then retry.
4. Wait a bounded time for shutdown acknowledgement. If the task is settled and no required operation is still running, use `TaskStop` by teammate name as a force-stop fallback when the tool is available and confirm the teammate stopped. Record graceful shutdowns, force-stops, and any unconfirmed timeout separately.
5. Do not call removed team cleanup tools; Claude Code owns cleanup and retention.
6. Leave no idle Opus teammates or unresolved shared tasks after the feature is closed. An unconfirmed stop prevents `done` and must be reported as `done-with-risks` when the implementation is otherwise complete.

## Teammate Health and Restart

Treat teammates as replaceable role sessions.

If a teammate goes idle without a delivered result, triage before any correction or replacement:

1. Check its shared task state. An untouched task usually means the memo was never sent with `SendMessage`, not that the role work failed.
2. Read the teammate's transcript to recover undelivered work. Turn-ending text is not delivered to the lead, so a finished memo often waits there: identify the teammate's session through the members of `~/.claude/teams/<team>/config.json` (read-only) and read the matching session file under `~/.claude/projects/`, or ask the user to open the teammate's pane. Treat a recovered memo as the deliverable.
3. Send one direct message telling the teammate to deliver the memo with the `SendMessage` tool and settle its owned task before going idle.
4. Escalate below only when the transcript shows no usable work or the teammate stays unresponsive after that nudge. Do not conclude teammates cannot reply or fall back to lead-only passes without completing this triage.

If a teammate is stale, confused, in the wrong role, using the wrong model, ignoring constraints, looping, or producing low-quality output:

1. Try at most one concise correction if the issue is minor.
2. For material issues, ask the teammate to shut down by name. If it does not stop after a bounded wait and no required operation should continue, use `TaskStop` by name and confirm the force-stop when available.
3. Spawn a replacement only after the old session is confirmed stopped, using the same named `team-pl-*` agent type and a runtime suffix such as `-r2`, not a generic teammate. If stop cannot be confirmed, do not spawn a replacement in the same session; use a new Claude session or continue lead-only and record the overlap risk.
4. Give the replacement a clean restart brief:
   - Current feature request
   - Relevant repo and memory facts
   - Accepted PL decisions so far
   - The exact role question
   - What to ignore from the stale teammate output
5. Record the restart in the feature note under Discussion Summary or Open Questions.

Do not rely on `/model` or later prompts to repair a wrong-model teammate. Check for an invocation model override, `CLAUDE_CODE_SUBAGENT_MODEL`, and a higher-priority same-name definition. Remove the override when possible; replace the teammate only after the cause is resolved. Otherwise use the recorded lead-pass fallback rather than looping.

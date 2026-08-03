---
name: run-meeting-report
description: Generate a meeting report on demand (outside the schedule) using the user's saved pcs-meeting-notes configuration. Use when the user says "run my standup report now", "generate my meeting notes for a custom window", "rerun this week's report", or wants a one-off work summary before setup of a new recurring meeting.
---

# Run Meeting Report (on demand)

Generate one report NOW using the user's saved configuration, without touching the
scheduled tasks.

1. Read `%USERPROFILE%\.claude\pcs-meeting-notes\config.json`. If it doesn't exist, stop
   and point them to `/setup-meeting-reports` — this skill has nothing to run from.
2. Ask which configured meeting to run (numbered list), or accept a custom one-off window
   ("cover Tuesday through right now"). For a scheduled meeting run on an off-day, apply
   the manual-run rule: most recent scheduled window end, normal start — and say which
   window you used.
3. Execute the full pipeline exactly as the personalized report prompt specifies —
   `reference/report-prompt-template.md` filled with this user's config (sources enabled,
   exclusions honored, read-only posture, own-work-only). All mechanics in
   `reference/source-mechanics.md` apply. **Recompute "today" from the system clock first.**
4. Write the same Detailed and/or Quickfire .docx outputs to the same Drive + local backup
   folders per `reference/output-format.md`. If a file for that meeting/date already exists
   (e.g. re-running after feedback), confirm before overwriting TODAY'S file — never touch
   older dates.
5. Deliver the file(s) in chat and close with the 3 most meeting-worthy items.

This skill is also the fix-it path: if a scheduled run missed something, the user can say
what was missed, you find it (the mechanics doc's lessons usually explain the miss), fold
it in, regenerate today's report, and — if the miss reveals a systemic gap — suggest the
corresponding prompt improvement for their scheduled tasks.

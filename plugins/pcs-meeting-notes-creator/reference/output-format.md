# Output Format — the two report versions

Both are .docx built with python-docx (Calibri 11 base). Filenames carry the meeting name
and run date; folders are calendar-week Monday-to-Sunday ranges:

```
<Drive or local root>\Work Summaries\<YYYY>\<Monday YYYY-MM-DD> to <Sunday YYYY-MM-DD>\
    <Meeting Name> Detailed <YYYY-MM-DD>.docx
    <Meeting Name> <YYYY-MM-DD>.docx          <- the Quickfire version
```

Primary delivery = the user's mounted Google Drive; a local backup copy is ALWAYS written
too (config holds both roots). Old files are never modified.

## Detailed version
- **Opens with a provenance paragraph** (italic): "This summary was prepared by Claude on
  <name>'s behalf, based on their Claude work sessions and project files, the emails they
  sent, their Google Chat messages, their Jira activity in <projects>, and their Google
  Drive file activity between <window start> and <window end>." — listing ONLY the sources
  actually enabled, and noting anything relevant (e.g. "user was out of office Thu-Mon").
- Grouped by **project/workstream**, not by source. Each section: what was worked on,
  outcomes shipped, key decisions, with related email/chat/Jira/Drive activity woven in.
- Separate small sections for email threads / chat conversations / Jira tasks not tied to
  a project.
- Closes with **Open threads / next steps**.
- First-person framing of the user's work; complete sentences; skimmable by a manager who
  wasn't there.
- **No exact figures or metrics** EXCEPT percent-progress-to-complete on large,
  long-running projects. (Meetings don't need numbers recited; progress percentages on
  big initiatives are the exception.)

## Quickfire version
- Bullet-pointed, **about one page**, minimal detail — built to get the user's work across
  fast, readable aloud.
- Grouped by project, 1-2 punchy bullets each. Plain confident language, no jargon that
  needs explaining, not overly formal.
- Ends with a short **"Blockers / Needs decision"** list and a **"Next up"** (or
  "Coming up") list.

## Tone calibration
Ask the user at setup (and adjust after their first real report) — some meetings want
formal, some want plain-spoken. Default: conversational-professional, confident, zero
fluff. The Detailed version is the same voice with room to explain.

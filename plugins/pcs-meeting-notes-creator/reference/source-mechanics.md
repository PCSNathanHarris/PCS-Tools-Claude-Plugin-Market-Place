# Source Mechanics — hard-won lessons baked into every report run

These were each learned the expensive way during the original build. The report prompt
template already encodes them; this doc is the "why" for anyone editing prompts.

## Time
- **Recompute "today" from the system clock at run start.** Long sessions cross midnight;
  a stale "today" silently pulls the wrong day (this happened: a request for "today's"
  messages pulled yesterday's).
- Manual "Run now" on a different weekday than scheduled: use the most recent scheduled
  window rather than guessing — and print the window in the report.
- Convert local windows to UTC RFC3339 for the chat puller (11:00 AM PDT = 18:00Z).

## Claude session transcripts
- `jq` is not on these machines. Stream with Python (`python`, never `python3` on Windows —
  the Store alias breaks it), `json.loads` per line, extract user messages + assistant text
  blocks only. Never load a whole JSONL (they reach 100+ MB).
- Set `PYTHONIOENCODING=utf-8` or emoji in transcripts crash printing on cp1252.
- Cowork transcript paths exceed Windows' 260-char limit — prepend `\\?\` to absolute paths
  in `open()` or you get FileNotFoundError on files that exist.
- **Extract ALL in-window messages per session, not opening/closing samples** — long
  sessions hold many workstreams; sampling misses mid-session work (this happened: an
  entire reporting-system build was invisible to the first report).
- Cloud-synced folders (OneDrive/Drive) refresh mtimes on unchanged files — confirm content
  is genuinely new (CreationTime or content inspection) before reporting a file as changed.

## Gmail
- `before:` is EXCLUSIVE — query the day after the window end, then filter precisely by
  timestamp.
- Page through ALL results with pageToken; never stop at page one.
- Thread search previews show only ~5 messages of a thread — a June-looking preview can
  hide in-window messages 50 deep. Always fetch the thread when its preview is stale.
- FULL_CONTENT thread fetches can exceed 8 MB and get persisted to a tool-result file —
  parse with streaming Python (take `plaintextBody`, strip quoted history), never Read raw.
- **Never classify mail from big-company domains as "automated."** google.com/route.com/
  creditkey.com correspondence with a named human is real work (this happened: an entire
  active vendor project lived in a thread the first run skipped). "Automated" = no-reply /
  notification senders only.

## Google Chat
- Everything via the local read-only puller (`chat_pull.py` in the user's config dir);
  see `google-chat-setup.md`. Exclusions apply BEFORE fetch.
- The puller marks the user's messages `is_me` — identity via OIDC sub == Chat user id.
- People API directory sweep resolves display names; results cache in `names_cache.json`.
- If the puller fails, the report notes the gap and continues — never stall, never re-auth
  unattended, never fall back to a browser.

## Jira
- "Their activity" = issues they created in-window, OR commented on in-window, OR edited
  (changelog author) in-window. Query issues updated in the window for the tracked
  projects, then filter by the user's accountId in changelog/comments.
- Report work-done summaries per issue — never field-level change listings.
- PROM is write-protected company-wide. Read-only, always, for everyone.
- Large JQL results persist to a tool-result file — parse with streaming Python.

## Google Drive
- `list_recent_files` with `orderBy: lastModifiedByMe` approximates "their" activity;
  paginate and filter by window. Exclude the report files these tasks generate.
- The Drive connector can create files but cannot edit/rename/organize — the mounted
  `G:\My Drive` is the reliable write path for delivery.

## Output
- python-docx builds the reports (installed at setup). Date in filenames = run date.
- Never modify or delete older report files — the week folders are an archive.
- Completion note always carries the file paths + top 3 meeting-worthy items.

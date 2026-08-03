# Google Chat Setup (the involved one)

## The warning to give the user, verbatim-ish

> "Google Chat is the one source that needs extra setup — it's more involved than the
> others. Google doesn't offer a simple connector for Chat, so we use a small read-only
> program with your own Google sign-in. One time, it takes roughly 2-10 minutes: you'll
> approve a Google permission screen with your own account (read-only — it can see your
> chats but can never post, edit, or delete anything), and depending on setup you may
> need a short visit to the Google Cloud console. After that it runs itself forever.
> Want to include Google Chat, or skip it for now? You can always add it later."

If they decline: proceed without chat, note in config `"chat": false`, and move on. No pressure.

## If they proceed — two paths, try in this order

### Path A — shared company OAuth client (fast, ~2 minutes)
Nathan owns a GCP project (`pcs-chat-reader`) with the Chat + People APIs already enabled
and an Internal OAuth client. If the user can obtain the `client_secret.json` for it
(ask Nathan — he distributes it privately via Drive, it must NEVER be committed to this
repo or pasted into chat):
1. Copy `scripts/chat_pull.py` from this plugin into the user's config dir
   (`%USERPROFILE%\.claude\pcs-meeting-notes\`). The plugin folder is a read-only cache —
   the script must run from the config dir so its token lives there.
2. Place `client_secret.json` in the same config dir.
3. Run: `cd "<config dir>" && python chat_pull.py auth` — their browser opens Google's
   consent screen; THEY sign in and approve with their own account. This mints `token.json`
   (theirs alone — the shared client identifies the app, the token scopes access to THEIR
   chats only).
4. Test: `python chat_pull.py pull --days 7` — confirm sensible message counts and that
   DM names resolve. If names show as raw user IDs, the People API needs a minute to
   propagate; retry once.

### Path B — their own GCP project (~10 minutes, needs console access)
Only if Path A isn't available. Walk them through console.cloud.google.com signed in with
their work account:
1. Create a project (suggest `pcs-chat-reader-<firstname>`).
2. APIs & Services -> Library -> enable **Google Chat API** AND **People API** (both —
   People API resolves teammate names; forgetting it is the #1 miss).
3. OAuth consent screen -> User type **Internal** -> app name "PCS Chat Reader" -> Save.
4. If the Chat API shows a Configuration tab demanding app details: fill name/avatar/
   description, do NOT enable interactive features.
5. Credentials -> Create credentials -> OAuth client ID -> **Desktop app** -> Download JSON
   -> save as `client_secret.json` in their config dir.
6. Then steps 1, 3, 4 from Path A.

## Facts the assistant needs while operating this

- Scopes are read-only by construction: `chat.spaces.readonly`, `chat.messages.readonly`,
  `chat.memberships.readonly`, `directory.readonly`, `openid`. The token physically cannot
  post.
- `excluded_spaces.json` (same dir) lists personal spaces excluded BEFORE fetch — their
  content never touches disk. The privacy pass populates this.
- `token.json` and `client_secret.json` are credentials: local only, never echoed, never
  synced to a shared location, revocable anytime at myaccount.google.com/permissions.
- Enabling an API in the console can take a few minutes to propagate — a 403 "API has not
  been used in project" right after enabling just means wait and retry.
- Attachments in chat ARE retrievable read-only via
  `svc.media().download_media(resourceName=attachment.attachmentDataRef.resourceName)` —
  useful when a user asks "find me that file from chat".
- If auth breaks later (revoked token), report tasks note the gap and continue — they never
  stall a report on chat and never attempt re-auth unattended.

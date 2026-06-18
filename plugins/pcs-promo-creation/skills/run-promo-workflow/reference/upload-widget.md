# Document uploads — always surface the drag-and-drop artifact

Whenever this workflow **needs a document or offers to load one as the next
step**, present the interactive **file-upload artifact** (the drag-and-drop
dropzone that renders inline in the chat) — never a plain "paste the path"
ask. Dropping a file there attaches it to the conversation exactly like the
chat `+` button, so you can read it like any other attachment.

## The doc-request points (surface the artifact at each)

| Stage | Ask for | Render |
|-------|---------|--------|
| Step 1 | Vendor promo **deck** (`.pdf`/`.png`/`.jpg`) **+** pricing **cheat sheet** (`.csv`/`.xlsx`) | one form, two dropzones |
| Step 3 | **NetSuite** "Promo Kit Support" **export** (`.xls`/`.csv`) | one form, one dropzone |

If you ever add another step that needs a file, surface the artifact there too —
this is the standing convention, not a per-step special case.

## Recreate the widget on every (re)prompt

The widget is **ephemeral** — once it scrolls up the chat it can't be reused.
Every time you arrive at (or **return to**) a file-request point, render a
**fresh** widget:

- After the operator hits **Skip**, says "not yet", or does anything else in
  chat and the workflow comes back to asking for that file → render it again.
- Never tell the operator to "use the box above" or wait on a stale widget.
- The **only** time you skip rendering is when the needed file is **already
  attached** (step 1 below). Don't nag for a file you already have.

## How to render it

The artifact is an **elicitation widget**. To render it:

1. **Infer first.** If the needed file is already attached to the conversation
   (the operator dropped it before/while invoking the skill), **skip the widget**
   and use the attachment. Only surface the dropzone for files you don't have —
   and when you do, render a **fresh** widget each time you (re)reach this point,
   never a pointer to an earlier one.
2. Call `mcp__visualize__read_me` with the `elicitation` module once to load the
   current canonical chrome (the File header anthropicon + the Upload dropzone
   SVG are fixed chrome — emit them byte-for-byte from what read_me returns).
3. Render the form with `mcp__visualize__show_widget` (HTML mode). Use one
   `.elicit-group` per file, each with the canonical `.elicit-files` dropzone and
   a textarea fallback (so the operator can paste text if they have no file).

Skeleton (fill the canonical SVGs from read_me; one `.elicit-group` per file):

```html
<form class="elicit">
  <div class="elicit-header">
    <svg><!-- canonical File anthropicon from read_me --></svg>
    <span>Promo deck details</span>
  </div>
  <div class="elicit-body">
    <div class="elicit-group">
      <label class="elicit-question">Drop the vendor promo deck (PDF/PNG/JPG):</label>
      <div class="elicit-files" data-name="deck">
        <label class="elicit-dropzone">
          <svg><!-- canonical Upload anthropicon from read_me --></svg>
          <span>Choose file</span>
          <input type="file" multiple>
        </label>
      </div>
    </div>
    <div class="elicit-group">
      <label class="elicit-question">Drop the pricing cheat sheet (CSV/XLSX) — optional:</label>
      <div class="elicit-files" data-name="cheat_sheet">
        <label class="elicit-dropzone">
          <svg><!-- canonical Upload anthropicon from read_me --></svg>
          <span>Choose file</span>
          <input type="file" multiple>
        </label>
      </div>
      <textarea class="elicit-textarea" data-name="cheat_sheet_text"
        placeholder="or paste SKU/price rows here"></textarea>
    </div>
  </div>
  <div class="elicit-footer">
    <button type="button" class="elicit-skip">Skip</button>
    <button type="button" class="elicit-submit">Continue</button>
  </div>
</form>
```

Keep the explanatory text (what the deck is, why) in your normal chat message —
the widget holds only the form. Follow all the elicitation rules from read_me
(locked composition, no `<script>`, byte-for-byte chrome).

## After the operator submits

Submitted files are **attached to the conversation** (you'll see e.g.
`Deck: milwaukee_q3.pdf (attached)` in the payload). Read them via the
conversation attachments like any uploaded file. A textarea fallback comes back
as text in the payload. If they hit **Skip**, fall back to asking in plain text.

## Fallback

If the visualize/Imagine widget tools aren't available in the session, don't
block — ask for the upload in plain text instead and proceed when the file is
attached. The artifact is the preferred experience, not a hard requirement.

## What this does NOT replace

The upload artifact is for **collecting documents only**. It is **not** a gate —
the Yes/No stage gates and the Jira `WRITE TO PROM` confirmation stay as
plain-text confirmations the operator types. Don't fold a gate into the widget.

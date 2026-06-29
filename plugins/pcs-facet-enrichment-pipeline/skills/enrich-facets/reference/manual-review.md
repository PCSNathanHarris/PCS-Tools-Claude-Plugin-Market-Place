# Reference — Manual review of uncertain values (in-chat, accept/reject)

The scraper writes high-confidence values straight through but **holds every uncertain value**
(see the AUTO/REVIEW split in `pdp-backfill-script.md`). This step shows those held values to the
operator **in the chat window**, lets them accept or reject each, then the import is built from the
survivors. This **replaces the old GATE 2** — submitting the review *is* the go-ahead to build + upload.

If `*_review_queue.json` is missing or empty, there is nothing to review: skip straight to the
NetSuite-format step.

## Input — `*_review_queue.json`

A list of held items, each:

| field | meaning |
|-------|---------|
| `item_id` | stable key, `"<internal_id>::<attribute_key>"` |
| `internal_id` | NetSuite Internal ID (row join key) |
| `product_title` | `Input Product Name` |
| `attribute_key` / `attribute_label` | the facet (key + display Name) |
| `proposed_value` | the value the scraper would have written |
| `source_url` | the PDP the value was read from |
| `source_kind` | `brand_pdp` or `retailer` |
| `why_pulled` | one line: what was read, from where |
| `review_reasons[]` | why it needs a look (retailer-sourced / normalized / inferred-from-prose / out-of-dropdown / multiple-candidate) |

## The artifact

Render an interactive accept/reject card list **in chat** so the operator reviews quickly. Each card
shows exactly what the operator asked for: **product title, the proposed `Label: value`, a clickable
link to the source PDP, why it was pulled, and why it needs review** — with an Accept/Reject toggle.

Mechanism (the `interactive` Imagine module — it allows the `<script>` + `sendPrompt()` this needs;
the `elicitation` module does **not**, so don't use it here):

1. Call `mcp__visualize__read_me` with the `interactive` module once (loads the current design system).
2. Read `*_review_queue.json` and render with `mcp__visualize__show_widget` (HTML mode), emitting **one
   card per item** with the data baked in. **Default every toggle to Accept** (operator flips the bad
   ones or hits "Reject all"). Keep explanatory prose in your chat message, not the widget.
3. On **Submit**, the widget calls the `sendPrompt()` global with a compact, parseable payload (below).

Skeleton (fill the card loop from the queue; set `BRAND` and `BATCH`):

```html
<style>
  .sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .rev-head{position:sticky;top:0;background:var(--surface-0);padding:10px 0;display:flex;
    gap:10px;align-items:center;flex-wrap:wrap;border-bottom:.5px solid var(--border-strong)}
  .rev-card{border:.5px solid var(--border-strong);border-radius:10px;padding:12px 14px;margin:10px 0;background:var(--surface-2)}
  .rev-title{font-weight:600;color:var(--text-primary)}
  .rev-val{margin:4px 0;color:var(--text-primary)} .rev-attr{color:var(--text-secondary)}
  .rev-meta,.rev-reason{font-size:13px;color:var(--text-secondary);margin:2px 0}
  .rev-reason{color:var(--text-danger,#b4232a)}
  .rev-toggle{margin-top:8px;display:inline-flex;gap:6px}
  .rev-toggle button{padding:5px 12px} .rev-toggle .is-on[data-act=accept]{border-color:var(--border-accent);background:var(--bg-accent)}
  .rev-toggle .is-on[data-act=reject]{border-color:var(--border-danger,#b4232a);background:var(--bg-danger,#fbeaea)}
</style>

<h2 class="sr-only">Review uncertain facet values for {{BRAND}}: accept or reject each before the NetSuite import is built.</h2>

<div class="rev-head">
  <strong>Review uncertain values — {{BRAND}}</strong>
  <span id="count" style="color:var(--text-secondary)"></span>
  <span style="flex:1"></span>
  <button id="allAccept">Accept all</button>
  <button id="allReject">Reject all</button>
</div>

<div id="cards">
  <!-- repeat per item -->
  <div class="rev-card" data-id="{{item_id}}">
    <div class="rev-title">{{product_title}}</div>
    <div class="rev-val"><span class="rev-attr">{{attribute_label}}:</span> {{proposed_value}}</div>
    <div class="rev-meta">{{why_pulled}}</div>
    <div class="rev-reason">Needs review: {{review_reasons joined with ", "}}</div>
    <a href="{{source_url}}" target="_blank" rel="noopener">View source PDP ↗</a>
    <div class="rev-toggle">
      <button class="t-acc" data-act="accept">Accept</button>
      <button class="t-rej" data-act="reject">Reject</button>
    </div>
  </div>
  <!-- /repeat -->
</div>

<div style="position:sticky;bottom:0;background:var(--surface-0);padding:10px 0;text-align:right">
  <button id="submit">Submit decisions →</button>
</div>

<script>
(function(){
  const state={};
  document.querySelectorAll('.rev-card').forEach(c=>state[c.dataset.id]='accept'); // default Accept
  function paint(){
    document.querySelectorAll('.rev-card').forEach(c=>{
      const v=state[c.dataset.id];
      c.querySelector('.t-acc').classList.toggle('is-on',v==='accept');
      c.querySelector('.t-rej').classList.toggle('is-on',v==='reject');
    });
    const ids=Object.keys(state), rej=ids.filter(k=>state[k]==='reject').length;
    document.getElementById('count').textContent=(ids.length-rej)+' accept · '+rej+' reject';
  }
  document.querySelectorAll('.rev-card .t-acc,.rev-card .t-rej').forEach(b=>
    b.addEventListener('click',()=>{state[b.closest('.rev-card').dataset.id]=b.dataset.act;paint();}));
  document.getElementById('allAccept').onclick=()=>{Object.keys(state).forEach(k=>state[k]='accept');paint();};
  document.getElementById('allReject').onclick=()=>{Object.keys(state).forEach(k=>state[k]='reject');paint();};
  document.getElementById('submit').onclick=()=>{
    const reject=Object.keys(state).filter(k=>state[k]==='reject');
    sendPrompt('REVIEW_DECISIONS '+JSON.stringify({brand:'{{BRAND}}',batch:'{{BATCH}}',reject:reject,accept_rest:true}));
  };
  paint();
})();
</script>
```

Widgets are **ephemeral** — re-render a fresh one whenever you return to this step; never point at a
stale one above.

## Submit payload → decisions

The Submit button sends one chat message:

```
REVIEW_DECISIONS {"brand":"Guardian","batch":"1/1","reject":["1234::material","1290::application"],"accept_rest":true}
```

When you (Claude) receive a message starting with `REVIEW_DECISIONS`, parse the JSON: every queue
`item_id` **not** in `reject` is **accepted** (default-Accept). Write `*_review_decisions.json`:
`{ "<item_id>": "accept" | "reject", ... }` covering every item in the queue.

The operator may also just **type** their decision ("reject the two material guesses", "reject 3 and 7",
"accept all"). Honour free-text the same way; when they reference list numbers, they mean the card order.

## Text fallback (no widget tool)

If `mcp__visualize__show_widget` isn't available, don't block. Print the queue as a numbered list — for
each item: product title, `Label: value`, source URL, why pulled, and the review reason(s) — then ask the
operator to reply with the numbers to **reject** (default-Accept: "everything else ships"). Parse their
reply into `*_review_decisions.json` the same way.

## Batching

If the queue exceeds ~40 items, render in pages of ~40 (chunk, or group by attribute). Each page is its
own widget + Submit; accumulate decisions across pages into one `*_review_decisions.json` before building.

## Merge into the import

Build the NetSuite file from **AUTO values + accepted review values**; rejected values are dropped
(their cells stay blank). For each **accepted** item, when generating the NS-format input (the short
script in `netsuite-format.md`), inject `"<attribute_label>: <proposed_value>"` into the next empty
`Facet` cell of the row whose `Internal ID == internal_id` (then the normal Product-Type-first ordering,
gap-compaction, and single-value collapse run as usual).

- **Accepted out-of-dropdown values** (`review_reasons` includes `out-of-dropdown`): include them in the
  import **and** append them to `*_dropdown_additions_needed.csv` with Suggested Action `operator-approved`
  so the attributes master can be updated later.
- **Rejected**: leave the cell blank; no other effect.

## Post-submit (the go-ahead)

Submitting the review **is** the approval — there is no separate GATE 2 Yes/No. Once decisions are
captured: build the final NS import, then upload the **whole** CSV to Drive exactly as
`netsuite-format.md` specifies. Report counts in Step 8: reviewed / accepted / rejected.

## Self-check before building

- Every queue `item_id` has a decision in `*_review_decisions.json` (no item silently dropped).
- Accepted values appear in the NS rows; rejected ones do not.
- Each accepted out-of-dropdown value is both in the import and logged `operator-approved`.
- The widget defaulted to Accept and offered Accept-all / Reject-all; a fresh widget was rendered on return.

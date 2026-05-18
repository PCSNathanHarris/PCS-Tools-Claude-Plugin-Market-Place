# Non-Included.csv handling

`<Vendor>-<QN>-<YYYY>-Non-Included.csv` contains every parser-excluded
row from the deck. Schema: `Page`, `Reason`, `SKU`, `Deal Text`,
`Detail`.

By default the skill does NOT create Jira Tasks from this file —
exclusions are parser self-documentation. A few `Reason` codes warrant
a manual-review prompt before deciding.

## Per-reason behavior

| Reason | Behavior | Notes |
|---|---|---|
| `brick-and-mortar` | **Auto-skip** | In-store only — not online. No Jira footprint. |
| `new-product` | **Auto-skip** | Vendor new-product launch, not a promo. |
| `spiff` | **Auto-skip** | Internal sales-rep incentive. Override flag if PCS later wants Jira visibility. |
| `killed` | **Auto-skip** | Cancelled deal. |
| `strikethrough` | **Auto-skip** | Per-SKU exclusion (parser handles inline). |
| `arp` | **Manual review** — prompt Y/N/Skip-all | Channel-restricted ARP deals; might need Jira tracking per case. |
| `pos-redemption` | **Manual review** | Mail-in / POS rebate; might still warrant a Jira footprint for monitoring. |
| `spend-to-earn` | **Manual review** | Threshold rebate; could be customer-visible online. |
| `image-only-free-good` | **Manual review** | Parser uncertainty — Nathan confirms whether to include. |
| `missing-price` (non-Makita) | **Manual review** | Paid SKU lost its price; might still warrant a Task with TBD pricing. |
| `buy-more-save-more` (BMSM) | **Out of plugin scope v0.1.0** | Manual workflow until parser emits a separate BMSM output. |
| `promo-code-only` (coupon) | **Out of plugin scope v0.1.0** | Manual workflow until parser emits a separate Coupon output. |

## Manual-review prompt format

For each row needing manual review, show:

```
[Non-Included row N of M] Reason: <reason>
  Page:  <Page>
  SKU:   <SKU or "(none)">
  Title: <Deal Text>
  Detail: <Detail>

Create a Jira Task for this anyway? (Y/N/Skip-all)
```

- `Y` — create the Task. Derive fields from `Deal Text` (Promo Name) and
  `Page` (description "Source: deck page N"). Use default Promo Type
  `Manufacturer NLP` for these — they're typically NLP-shaped exclusions.
  Label as `NLP`.
- `N` — skip just this row.
- `Skip-all` — skip every remaining manual-review row this run.

## Auto-skip logging

Auto-skipped rows are silent on the console BUT recorded in the audit
log:

```
SKIP non-included row N: reason=<reason> auto-skipped per non-included.md
```

End-of-run summary shows the auto-skip count grouped by reason:

```
Auto-skipped (Non-Included): 11
  brick-and-mortar: 4
  new-product: 5
  spiff: 1
  killed: 1
```

## Future direction

When the parser is updated to emit dedicated `BMSM.csv` and `Coupon.csv`
files (currently both route to `non_included.csv`), this skill will
gain handling for them. For v0.1.0, both stay manual.

The `non-included` file structure has remained stable across parser
versions (5 columns). If the parser adds new `Reason` codes, this table
needs updating — until then the skill defaults unknown reasons to
manual review with a clear "unknown reason" warning.

## RSAs are separate (not in this file)

RSA promos come from `RSA-Kits.csv` / `RSA-NLP.csv`, NOT from
`Non-Included.csv`. RSA review handling is documented in
`SKILL.md` Step 6 and `field-mapping.md` — every RSA row gets the
same `Y/N/Skip-all` prompt before Task creation, regardless of what's
in this file.

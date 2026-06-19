# NLP consolidation — one Task per vendor/quarter + per-date-group sub-tasks

**v0.3.0.** Replaces the old "one Task per NLP Promo Name." Applies to **non-RSA**
NLPs only (`NLP-Sheet.csv`). **RSA-NLP stays per-row** — it carries a `Credit Amount`
and is reviewed individually (POS Redemption = Yes, Online Execution = No).

## Structure

For each **vendor** in the run (one quarter per run):

1. **One parent Task** for all of that vendor's `NLP-Sheet.csv` rows.
   - Summary: `<YYYY> <Period> - NLPs` per `naming-rules.md` N4.
   - Start (`customfield_10015`) = the **earliest** `Online Execution Start` across all rows.
   - Due (`duedate`) = the **latest** `Online Execution End` — the last takedown day.
   - Promo Type (`Manufacturer NLP`) / Online Execution / POS / parent Epic / labels per
     `field-mapping.md` (Shared field derivations).
   - Description: short intro + the list of date groups (sub-tasks) + the overall window.
     The full SKU detail lives in the per-group CSV attachments, not the task body.

2. **A sub-task per date group.** Group the vendor's NLP rows by the tuple
   `(Online Execution Start, Online Execution End)` = `(start, takedown)`. Each distinct
   pair is one date group → one sub-task under the parent.
   - Sub-task summary: literal `MM/DD-MM/DD` (Rule N9) of that group's window.
   - Sub-task start / due = that group's start / takedown.

## The two CSVs per sub-task (generate, then attach)

For each date-group sub-task, **generate two CSVs** with a short throwaway script
(read `NLP-Sheet.csv`, filter to that group's rows, write the CSVs into the session
folder), then **attach both to that sub-task** via the Jira REST path
(`reference/integrations.md`; needs the token). If no token, still write them to the
session folder and note in the sub-task description that they're local — CSVs are not
secrets.

1. **Start-date pricing** — `<Vendor>-<QN>-<YYYY>-NLP-<MMDD>-<MMDD>-pricing.csv`
   Columns: `SKU`, `New Promo Price`, `Price Label`. One row per NLP-Sheet row in the
   group. Blank `Promo Price` → `TBD` + a "needs manual pricing" note (as today). This
   is the "set the new price on the **start** day" file.
2. **Revert / takedown schedule** — `<Vendor>-<QN>-<YYYY>-NLP-<MMDD>-<MMDD>-revert.csv`
   Columns: `SKU`, `Revert Date` (= the group's takedown / `Online Execution End`).
   **No prices** — the original/revert price is **not** in parser data; it comes from
   **NetSuite later**, so this is a schedule, not a priced file. First line is a header
   comment: `# Revert prices sourced from NetSuite at takedown — schedule only.` This is
   the "revert the price on the **takedown** day" reminder.

## Notes

- Never drop a SKU — blank-price rows still appear in the pricing CSV (`TBD`).
- One parent per vendor. (A deck is one vendor, so usually one parent per run; if a run
  spans multiple vendors' NLP-Sheets, make one parent each.)
- This is the **only** place that consolidates across Promo Names. Kit / Other-Promotions
  grouping is unchanged (`field-mapping.md`).

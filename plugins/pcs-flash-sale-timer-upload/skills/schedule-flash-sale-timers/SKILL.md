---
name: schedule-flash-sale-timers
description: Weekly routine that schedules Milwaukee flash sale deal timers on Toolup and Red Tool Store. Reads the Milwaukee Flash Sale Google Calendar, works out what goes live this week and what can now be scheduled ahead, and writes countdown_date_start/end to each flash sale collection - skipping anything already correct. Use for the Monday 3:40 PM routine, or whenever someone asks to set, schedule, re-check or fix a Milwaukee flash sale deal timer or countdown, mentions the Milwaukee Flash Sale calendar, a mil-2026-WeeklyFS or mil-weeklyFS tag, or a countdown_date_start / countdown_date_end metafield.
---

# Schedule Milwaukee flash sale deal timers

Weekly routine. Set the countdown timers for Milwaukee flash sales on the two stores
that run them. **Timers live on the collection. Products are never touched.**

**Runs every Monday at 3:40 PM Pacific.** Most categories will already be correct from a
previous run — that is the expected outcome. The run exists to catch calendar changes and
to schedule each category's next sale once its current one has ended. Safe to re-run at
any time; it only writes where something differs.

## Scope — two stores only

| Store key | Brand | Public domain |
|---|---|---|
| `toolupstore` | Toolup | toolup.com |
| `the-milwaukee-store` | Red Tool Store | redtoolstore.com |

`toolup-my-tool-store` is My Tool Store and is **never** in scope. State the store key
explicitly before any write.

## Step 1 — Read the calendar

Source of truth is the **Milwaukee Flash Sale** Google Calendar:
`c_fd2d696c16f3cbac37e0697fc0f0908659a7b256e76048bdd76e25f1e2ba6d26@group.calendar.google.com`

Events are titled `Milwaukee FS - <Category> (Day 1/2)` and `(Day 2/2)` on two
consecutive days.

**The Calendar MCP `list_events` tool has been observed failing persistently.** If it
errors, do not keep retrying — read the calendar through the Chrome browser tools, which
use the operator's logged-in Google session:

```
https://calendar.google.com/calendar/u/0/r/search?q=Milwaukee%20FS
```

Then `get_page_text`. That returns every scheduled sale with dates in one page.

Reconcile the count the UI reports before trusting the read:

```
total reported = (sales x 2 day-events) + Email Schedule entries matching the search
```

If it does not balance, events were missed — say so rather than proceeding on a partial
read.

## Step 2 — Compute the target window

Every flash sale is **exactly 48 hours**, anchored to 9:00 PM Pacific because that equals
midnight Eastern — the moment the pricing drops.

```
start = (Day 1/2 date - 1 day)  at 21:00 Pacific
end   = (Day 2/2 date)          at 21:00 Pacific
```

A calendar-marked Tue + Wed sale starts **Monday 9:00 PM** and ends **Wednesday 9:00 PM**.

Write ISO 8601 with an **explicit Pacific offset**. Never send a naive datetime.

- `-07:00` (PDT) between the second Sunday in March and the first Sunday in November
- `-08:00` (PST) otherwise

Operators say "9pm PST" year-round but always mean Pacific wall-clock. In summer that is
`-07:00`; taking "PST" literally puts every timer an hour late. Sales run Tue-Wed or
Thu-Fri and DST changes fall on Sundays, so start and end always share one offset.

Shopify stores and returns the offset exactly as written; it does not normalize to UTC.

**End is 9:00 PM, never 11:59 PM.** Some historical collection values end at 11:59 PM and
some start on Day 1 rather than the day before. Those are known mistakes. Do not copy
them, and do not raise them as a question.

### Which occurrence is the target

A collection holds exactly one start/end pair, so each category has one correct value at
any moment. For each of the six categories:

1. Find any occurrence where `start <= now < end`. That sale is **live** — the collection
   must keep showing it. Do not touch this category. Its next sale becomes schedulable
   once this window closes, i.e. on a later run.
2. Otherwise the target is the **soonest occurrence whose start is in the future**.

That rule is what makes the routine safe to run weekly: a live sale is never overwritten,
and a category frees up on its own the run after it ends.

## Step 3 — Compare, then decide

Read what each collection currently holds:

```
shopify_get_collection_metafields  store, handle
```

Compare against the Step 2 target:

- **Identical** → skip. No write. This is the common case.
- **Different or absent** → act. Either it has never been scheduled, or the calendar moved
  and the stored window is now wrong.
- **Category is live** → skip, and report that it is live and when it frees up.

Report the tally every run: acted, already correct, skipped-live. A run where everything
is already correct is a successful run, not a wasted one.

## Step 4 — Write the collection metafields

Both stores use identical keys and types (`owner_type: COLLECTION`):

| Full key | Type |
|---|---|
| `custom.countdown_date_start` | `date_time` |
| `custom.countdown_date_end` | `date_time` |

One `shopify_bulk_set_metafields` call per store, `owner_type: "COLLECTION"`, two
assignments per collection. Each call returns a rollback file — record it.

**Do not filter products, and do not write any product metafield.** The collection's own
rules already enforce on-sale and in-stock, so the timer renders only on eligible items
automatically. No product snapshot is involved, which is what lets a window be scheduled
arbitrarily far ahead.

## Step 5 — Verify and report

Read back with `shopify_get_collection_metafields` on both stores and confirm values and
offsets. Then report:

- Which categories were written, with their windows and rollback filenames
- Which were already correct
- Which were skipped as live, and the date each frees up

## Category, tag and collection map

Six categories. **Two tag naming conventions are in use** — `mil-2026-WeeklyFS-*` and
`mil-weeklyFS-*` (no `2026-` segment). A wildcard on one prefix silently misses the other
and looks mathematically complete while doing so. Always search both:

```
tag:mil-2026-WeeklyFS*
tag:mil-weeklyFS*
```

Two categories are **split across two tags and two collections sharing one calendar event
and one window** — write both halves.

| Category | Tag(s) | Toolup collection | RTS collection |
|---|---|---|---|
| Accessories | `mil-2026-WeeklyFS-ACCY` | `black-friday-milwaukee-accessory-deals` | `black-friday-milwaukee-accessory-deals` |
| M12/M18 Combo Kits | `mil-2026-WeeklyFS-M12-Combo` + `mil-2026-WeeklyFS-M18-Combo` | `black-friday-milwaukee-m12-deals` + `black-friday-milwaukee-m18-deals` | same handles |
| M12/M18 Bare Tools | `mil-weeklyFS-m12-bare-tools` + `mil-weeklyFS-m18-bare-tools` | `black-friday-m12-bare-tools-flash-sale` + `black-friday-m18-bare-tools-flash-sale` | `black-friday-milwaukee-m12-bare-tools-flash-sale` + `black-friday-milwaukee-m18-bare-tools-flash-sale` |
| Hand Tools | `mil-weeklyFS-Hand-Tools` | `milwaukee-black-friday-hand-tool-flash-sale` | `milwaukee-black-friday-hand-tool-flash-sale` |
| Bundle Blowout | `mil-weeklyFS-1.8.26` | `milwaukee-bundle-blowout-flash-sale` | `milwaukee-black-friday-bundle-blowout-flash-sale` |
| OPE | `mil-2026-WeeklyFS-OPE` | `milwaukee-black-friday-ope-flash-sale` | `milwaukee-black-friday-ope-flash-sale` |

Handles contain `black-friday` for historical reasons. They are the **weekly** flash sale
collections regardless of the name — each was positively identified by the countdown
window it carried from its own category's previous run.

### Resolved collection IDs

| Category | Toolup | Red Tool Store |
|---|---|---|
| Accessories | `498787320099` | `291751723092` |
| M12 Combo | `498786140451` | `291751592020` |
| M18 Combo | `498786271523` | `291751624788` |
| M12 Bare Tools | `498921046307` | `291824664660` |
| M18 Bare Tools | `498921079075` | `291824697428` |
| Hand Tools | `498984157475` | `291966943316` |
| Bundle Blowout | `498984091939` | `291897442388` |
| OPE | `498984354083` | `291967139924` |

Re-resolve any ID with `shopify_get_collection_metafields` by `handle`. Passing a
namespace that matches nothing (e.g. `zzz`) returns the ID with almost no output.

`mil-weeklyFS-1.8.26` is date-stamped but is the durable Bundle Blowout tag across all its
runs; it does not correspond to any Bundle Blowout calendar date.

## Standing notes

**An empty flash sale collection is the normal pre-sale state — never flag it.**
The collections filter on `is_online_sale = true`, and the sale pricing drops at
**9:00 PM Pacific on go-live — the same instant the timer starts.** A collection scheduled
days ahead reads 0 products right up until go-live, then populates at exactly the moment
its countdown begins. The three events are simultaneous by design:

```
21:00 Pacific  ->  pricing drops  ->  is_online_sale flips true
               ->  products enter the collection
               ->  countdown_date_start is reached, timer renders
```

Consequences:

- Never use product count to validate a scheduled sale. It is 0 for every future sale and
  tells you nothing. Validate against the calendar and the stored window only.
- Never withhold or delay a write because a collection looks empty.
- Do not "wait until closer to go-live so the products are in there" — there is no moment
  before 9 PM when the collection is populated.

(Observed 2026-07-29: Hand Tools read 0 products against 778 tagged. Correct.)

**Expired values are inert.** The theme will not render a countdown before the start or
after the end. Never propose clearing stale collection values as housekeeping.

**New categories and tags will appear.** If the calendar shows a category not listed
above, find its tag by searching both prefixes and its collection by looking for one
carrying countdown history, then report the gap.

**The calendar runs out.** As of the 2026-07-29 read it was populated through Fri Aug 28,
2026. When the last scheduled sale is in the past, say so plainly instead of reporting
"nothing to do".

**Rollback.** Every write returns a rollback file. Undo with `shopify_list_rollbacks` then
`shopify_undo_operation`. Metafield sets are updates and are reversible.

If any step in a multi-store sequence fails: stop, report exactly what completed and what
did not with rollback filenames, and wait. Do not route around a failing tool.

## Background — why products are not touched

Kept as history. **None of this is part of the workflow. Do not perform any of it.**

Timers were originally written to **product** metafields (`custom.countdown_date_start` /
`_end` on each product), computed from a live eligibility query: tagged + on sale +
inventory > 0. That worked but had to be re-run the morning before every sale, because the
product set was a point-in-time snapshot.

It was replaced by collection-level timers because a product-level timer **suppresses**
the collection timer on that product. Once product timers exist, the collection cannot
drive the countdown.

Clearing them turned out to be impossible through this connector, which was the deciding
constraint:

- Setting the value to `""` → rejected: `INVALID_VALUE - Value must be in
  "YYYY-MM-DDTHH:MM:SS" format`
- Setting the value to `null` → rejected: `Expected value to not be null`

`shopify_bulk_set_metafields` wraps only the `metafieldsSet` mutation, whose
`MetafieldsSetInput` requires a non-null, format-valid value. A *set* cannot express
"remove". Removal needs `metafieldsDelete`, which this connector does not implement.

The residue was cleared out-of-band via Matrixify on 2026-07-29 (430 products on Toolup,
184 on Red Tool Store — a blank metafield cell on import deletes the value). With that
done, collections became the single source of truth.

**If a product-level countdown is ever found on a flash sale product again:** do not try
to clear it in-band, and do not fall back to product timers. Report it, and have it
removed via Matrixify or a `metafieldsDelete` capability added to the MCP server.

## Reference

Remaining 2026 schedule, a fully worked example, and hard-won pitfalls are in
`reference/flash-sale-schedule.md`.

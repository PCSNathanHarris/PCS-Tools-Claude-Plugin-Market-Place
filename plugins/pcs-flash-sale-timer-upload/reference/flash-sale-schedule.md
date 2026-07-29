# Flash sale schedule reference

Companion to `skills/schedule-flash-sale-timers/SKILL.md`.

Calendar read 2026-07-29. Scheduling then ran **Jan 13 through Fri Aug 28, 2026**
(56 sales). Re-read the calendar for anything later — the schedule is extended
periodically and this file will go stale.

## Reconciling a calendar read

The Calendar search UI reports a total event count. Reconcile it before trusting the
read:

```
total reported = (sales x 2 day-events) + Email Schedule entries matching the search
```

On 2026-07-29 that was `115 = 56 x 2 + 3`. If it does not balance, events were missed.

## Cadence

Two sales most weeks, on Tue-Wed and/or Thu-Fri. Consecutive sales **hand off at the
same instant** — a Tue-Wed sale ends Wed 9:00 PM and the Thu-Fri sale starts Wed
9:00 PM. One window's end equalling the next window's start is correct, not a bug.

Category frequency across the 56: Bundle Blowout 12, Accessories 11, Hand Tools 10,
M12/M18 Combo Kits 9, M12/M18 Bare Tools 9, OPE 5.

## Remaining 2026 schedule as read

Windows computed with the 48-hour rule. All in PDT (`-07:00`) — DST does not end until
Nov 1, 2026.

| Category | Calendar days | Write timers on | Start | End |
|---|---|---|---|---|
| Bundle Blowout | Thu Jul 30 – Fri Jul 31 | Wed Jul 29 | `2026-07-29T21:00:00-07:00` | `2026-07-31T21:00:00-07:00` |
| M12/M18 Bare Tools | Tue Aug 4 – Wed Aug 5 | Mon Aug 3 | `2026-08-03T21:00:00-07:00` | `2026-08-05T21:00:00-07:00` |
| Hand Tools | Thu Aug 6 – Fri Aug 7 | Wed Aug 5 | `2026-08-05T21:00:00-07:00` | `2026-08-07T21:00:00-07:00` |
| Bundle Blowout | Tue Aug 11 – Wed Aug 12 | Mon Aug 10 | `2026-08-10T21:00:00-07:00` | `2026-08-12T21:00:00-07:00` |
| M12/M18 Combo Kits | Tue Aug 18 – Wed Aug 19 | Mon Aug 17 | `2026-08-17T21:00:00-07:00` | `2026-08-19T21:00:00-07:00` |
| Accessories | Thu Aug 20 – Fri Aug 21 | Wed Aug 19 | `2026-08-19T21:00:00-07:00` | `2026-08-21T21:00:00-07:00` |
| OPE | Tue Aug 25 – Wed Aug 26 | Mon Aug 24 | `2026-08-24T21:00:00-07:00` | `2026-08-26T21:00:00-07:00` |
| Bundle Blowout | Thu Aug 27 – Fri Aug 28 | Wed Aug 26 | `2026-08-26T21:00:00-07:00` | `2026-08-28T21:00:00-07:00` |

Earlier 2026 sales (Jan 13 – Jul 24) are historical and omitted.

## Worked example — Bundle Blowout, executed 2026-07-29

Calendar: `Milwaukee FS - Bundle Blowout (Day 1/2)` Thu Jul 30,
`(Day 2/2)` Fri Jul 31. Tag `mil-weeklyFS-1.8.26`.

1. **Clear check.** 919 tagged products per store; `has_metafield` was 0 for both
   `countdown_date_start` and `countdown_date_end` on both stores. Nothing to clear.
   This also proved no product from the then-live OPE sale carried the Bundle tag.
2. **Write.** `owner_type: COLLECTION`, 2 assignments per store:
   - `toolupstore` → `gid://shopify/Collection/498984091939`
   - `the-milwaukee-store` → `gid://shopify/Collection/291897442388`
   - start `2026-07-29T21:00:00-07:00`, end `2026-07-31T21:00:00-07:00`
   - Both applied 2, errors 0. Rollback files
     `20260729_175138_bulk_set_metafields_toolupstore.json` and
     `20260729_175143_bulk_set_metafields_the-milwaukee-store.json`.
3. **Verify.** Read back on both stores; offsets preserved verbatim.

Both collections had held stale values from the Jul 16–17 run, overwritten by this
write.

## Pitfalls confirmed the hard way

**Two tag prefixes.** `mil-2026-WeeklyFS-*` covers Accessories, both Combo tags and
OPE. `mil-weeklyFS-*` covers Hand Tools, both Bare Tools tags and Bundle Blowout. A
wildcard on one prefix returns a mathematically complete-looking result while missing
the other entirely. Search both.

**Historical collection values are unreliable.** Of four collections carrying prior
countdown values, three started on Day 1 rather than the day before, and all four
ended at 11:59 PM instead of 9:00 PM. These are known mistakes. The rule in SKILL.md
is authoritative.

**Product counts are never a target.** Inventory and the on-sale flag move constantly;
tag pools range from ~29 to ~1,440 products. A count that differs from last time is
not an error. Under the collection-timer model you should not be counting products at
all except to check what needs clearing.

**Verifying render.** A correctly-set timer showing the expected remaining hours on a
live PDP is the real confirmation. On 2026-07-29 the OPE timers read "11 hours" at
about 9:15 AM Pacific against a 9:00 PM end — which is what proved the `-07:00` offset
choice was right rather than `-08:00`.

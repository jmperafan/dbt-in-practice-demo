---
name: draft-column-descriptions
description: Draft descriptions for a model's undocumented columns, from its compiled SQL and upstream column docs. Use when a model has columns with no description, or a blank description: "". Never ships a draft unread.
---

At the volume a model gets written at now, hand-writing every column
description is arithmetically impossible, not just tedious — but an
unreviewed draft is worse than no description, since it reads as
authoritative. This skill drafts; it does not ship.

1. Find the model's compiled SQL (`dbt show --inline` or the model file
   itself) and, for each column that traces back to an upstream `ref()` or
   `source()`, that upstream column's own description if one exists —
   cascade it rather than inventing a new one.
2. For a column with no upstream description to cascade (a calculation, a
   case statement, a surrogate key), draft one from the SQL itself: what
   grain is this, what populates it, when would someone reach for this
   column over a similarly-named one nearby. A description that just
   restates the column name (`"The member id"` for `member_id`) is
   worthless — write what Lesson 5's own `_dim_members.yml` style does.
3. **Stop. Do not write the YAML.** Print the drafted descriptions next to
   the column names, grouped by model, and say plainly how many columns
   got a draft.
4. Spot-check by criticality, not every draft equally: a column already
   covered by a doc block (`models/docs.md`) or appearing in a model this
   project certifies (Lesson 7) gets a real read; a column in an internal,
   low-traffic model can get a lighter pass. Say which tier a given batch
   falls into so the review effort actually matches the risk.
5. Only write the reviewed descriptions to the model's own `_<model>.yml`
   file (this project's one-file-per-model convention, Lesson 5.4), never
   a shared file multiple contributors are likely to edit at once.

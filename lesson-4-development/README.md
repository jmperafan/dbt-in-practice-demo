# Lesson 4: Development

**Start:** `git checkout lesson-4-start` · **Finish:** `git checkout lesson-4-end`

## The mental model

AI writes most of the SQL now, so this lesson is about managing the
complexity that's left: the technical kind, hidden until it breaks, and
the kind that's really a business call in disguise. Catch a defect as
early as it's cheapest to catch — shift-left economics, the well-documented
curve where the same mistake costs a fraction fixed at design versus caught
in production. This lesson's tools sit on that curve in build order:
config, then DRY SQL, then a macro, then a package, then the materialization
decision that only matters once a model actually has to run at scale.

**Verification status:** everything in this lesson was checked with
`dbt parse` and `dbt compile` against dummy Snowflake credentials — real
syntax and Jinja resolution, not yet a real warehouse run. One model,
`fct_court_reservations`, needs a live connection even to compile (see
4.7), which is the one thing left to confirm once the sandbox exists.

## 4.1 — dbt Config

Every model here sets its own config where it needs to, on top of the
per-directory defaults in `dbt_project.yml` (staging views, intermediate
ephemeral, marts tables): `fct_court_reservations` overrides
`materialized` to `incremental` right in the file (4.7), rather than a
project-wide config block trying to anticipate every exception.

## 4.2 — DRY SQL

[`macros/duration_to_hours.sql`](../macros/duration_to_hours.sql) exists
because three sources describe duration inconsistently (minutes in two
places, hours in a third) — the rule of three, not written the first time
a duration shows up, written once it's clearly a pattern.

**Enforced, not just advised:** this lesson adds a real guardrail,
[`scripts/check_no_select_star.py`](../scripts/check_no_select_star.py), a
`PreToolUse` hook in
[`.claude/settings.json`](../.claude/settings.json) that blocks a `Write`
or `Edit` introducing `select *` in a `.sql` file, before it ever lands on
disk. Verified directly: tested it against a blocking case, a passing
case, and a non-SQL file, all three behave correctly. The cost this
closes is the same either way, whether the diff came from a person or an
agent.

## 4.3 — dbtonic Jinja

[`models/intermediate/int_court_activity.sql`](../models/intermediate/int_court_activity.sql)
is the Jinja worth seeing here: three sources (reservations, lessons,
matches) describe the same underlying thing, time on a court, in three
different shapes. One `union all` of three CTEs, each calling the same
macro where it needs duration converted, gives every mart downstream one
shape to query instead of three.

## 4.4 — Building Reusable Macros

Same file as 4.2 — `duration_to_hours` is called three times across
`int_court_activity`'s lessons and matches CTEs (court_reservations
already has hours), each with its own rounding handled once, not
independently decided three times.

## 4.5 — dbt Packages

[`fct_court_activity`](../models/marts/fct_court_activity.sql) uses
`dbt_utils.generate_surrogate_key`, a real `dbt-labs/dbt_utils` macro
(already installed as a dependency of `codegen`, see
[`package-lock.yml`](../package-lock.yml)), for the one case in this
project where no single source column is unique across activity types:
checking the hub before hand-rolling a hash of several columns.

## 4.6 — Materializations

Four kinds, three used in this project so far: `view` (staging),
`ephemeral` (`int_court_activity`, inlined into whatever refs it, nothing
outside this project queries it directly), `table` (`dim_members`,
`dim_coaches`, `fct_court_activity`), and `incremental` (4.7). `dim_members`
and `dim_coaches` are plain tables on purpose: a membership and coaching
roster rebuilds cheaply in full every run, nothing about it needs
incremental logic's added complexity.

## 4.7 — Incremental Models

[`fct_court_reservations.sql`](../models/marts/fct_court_reservations.sql)
is this project's first incremental model, and the fact table that
actually earns it: `court_reservations` is the highest-volume,
highest-frequency source here (Lesson 3's tight freshness SLA). `merge` on
`reservation_id` is what keeps this correct given Lesson 3's deliberate
duplicate-row quirk in `stg_court_reservations` — a rerun merges onto the
existing row instead of doubling it.

**What I could and couldn't verify:** `dbt parse` and `dbt compile`
succeeded for every other model in this project (45 of 46). This one
failed to compile even with placeholder credentials, because
`is_incremental()` has to check whether `{{ this }}` already exists in the
target database, which needs a real connection, not just valid Jinja. That
check (and the `merge` behavior it gates) is the one piece of this lesson
genuinely unconfirmed until the Snowflake sandbox exists.

## What's next

```bash
git checkout lesson-5-start   # or: lesson-4-end, the same commit
```

Lesson 5 documents this project's growing mart layer properly: tags, meta,
doc blocks, and the YAML-management discipline that keeps descriptions
from going stale as `dim_members`, `dim_coaches`, and the two fact tables
here pick up real consumers.

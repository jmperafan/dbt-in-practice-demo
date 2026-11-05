# Lesson 3: Sources

**Start:** `git checkout lesson-3-start` · **Finish:** `git checkout lesson-3-end`

## The mental model

Most teams start here: raw tables appear, `sources.yml` written after the
fact if at all, nobody knows what the columns mean. The real model is a
data contract: an enforceable producer/consumer interface with four parts,
in this order: **schema** (what columns, what types), **quality**
(idempotent, no duplicates on rerun), **SLA** (a freshness window), and
**enforcement** (the gate that makes the first three real instead of
aspirational). A contract that isn't enforced is a wiki page nobody rereads.

This lesson builds that contract, end to end, against the nine raw tables
`scripts/load_raw_data.py` already landed in the `raw` schema.

## 3.1 — Defining Sources

[`models/staging/_raw__sources.yml`](../models/staging/_raw__sources.yml)
defines all nine. Each one's `loaded_at_field` and `freshness` block is the
SLA section of its contract; `data_tests: [unique, not_null]` on each
primary key is the schema section, checked on every `dbt build`.

## 3.2 — Staging Models

One job only: rename and cast, never drop a row or a column.
[`stg_court_reservations.sql`](../models/staging/stg_court_reservations.sql)
is the one genuinely interesting case in this project: `start_time` and
`end_time` arrive mixed, most rows a bare `"HH:MM"` string, about 15% a
full `"YYYY-MM-DD HH:MM:SS"` timestamp. The model normalizes both to one
real timestamp column instead of carrying the format problem downstream.
Every other staging model here is closer to a straight rename, because the
raw columns already came in clean, which is itself worth seeing: staging
isn't always complicated, it's complicated exactly where the source is.

## 3.3 — Generating Code with dbt-codegen

`dbt-labs/codegen` is in [`packages.yml`](../packages.yml). Two of its three
commonly-cited macros work on this project as-is:

```bash
dbt run-operation generate_base_model --args '{"source_name": "raw", "table_name": "members"}'
dbt run-operation generate_model_yaml --args '{"model_names": ["stg_members"]}'
```

**One doesn't: `generate_source` fails on DuckDB.** Verified directly: it
depends on `dbt_utils.get_relations_by_pattern`, which has no DuckDB
implementation and falls back to a `<database>.information_schema.tables`
query DuckDB doesn't support unprefixed catalogs that way. The error is
blunt (`Catalog Error: Table with name "information_schema.tables" does
not exist`), not a silent wrong answer, so you'll know immediately if you
hit it. `generate_base_model` and `generate_model_yaml` use
`adapter.get_columns_in_relation` instead, dbt's own cross-adapter API, and
both work cleanly here. Write a new source's YAML by hand on this project;
generate the staging model and its properties file as normal.

## 3.4 — Source Freshness

```bash
dbt freshness
```

Run it: all nine sources currently pass. `court_reservations` is the one
genuinely tight SLA in this project (`warn_after` 1 day, `error_after` 3
days), because an operational booking table should need same-day attention
if it stops loading; the rest are deliberately looser (roster and
tournament-record tables that get a routine sync, not a continuous feed).

**A display quirk worth knowing about, not a real bug:** `court_reservations`
may show something absurd like "584542046090 years ago" instead of a sane
duration. That's dbt v2 mishandling a *negative* age, when the most recent
`loaded_at` lands in the future relative to right now, which happens here
because of the deliberate late-arriving-row quirk (3.4's quality section).
The check still correctly reports **Passed**; only the human-readable
string is wrong.

## 3.5 — Key Takeaways

- Treat `sources.yml` as a data contract, not paperwork filed after the fact.
- Generate the mechanical parts (base models, properties YAML) with codegen;
  don't ask an AI to guess `information_schema` for you. On this project,
  know specifically which codegen macro that advice does and doesn't cover.
- Staging does one job. The complexity belongs to the source that earns it,
  not spread evenly across every model out of habit.

## What's next

```bash
git checkout lesson-4-start   # or: lesson-3-end, the same commit
```

Lesson 4 builds the first intermediate models and marts on top of this
staging layer, and converts `stg_court_reservations` into this project's
first incremental model.

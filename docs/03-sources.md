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

This lesson builds that contract against the nine raw, structured tables
`scripts/load_raw_data.py` lands in Snowflake's `RAW` schema (a tenth,
`member_feedback`, already exists from Lesson 2 — see 3.1).

**Verification status:** Lessons 1-2 were rewritten for Snowflake and
re-verified at the syntax level (`dbt parse` against dummy credentials);
this lesson's content hasn't been run against a real account yet either.
Treat the SQL and YAML here as correct, not yet confirmed.

## 3.1 — Defining Sources

[`models/staging/_raw__sources.yml`](../models/staging/_raw__sources.yml)
defines all ten (the nine from this lesson, plus `member_feedback`, which
arrived in Lesson 2 specifically because the context-engineering demo
needed real text before this lesson's turn). Each one's `loaded_at_field`
and `freshness` block is the SLA section of its contract;
`data_tests: [unique, not_null]` on each primary key is the schema
section, checked on every `dbt build`.

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

`dbt-labs/codegen` is in [`packages.yml`](../packages.yml), alongside
`dbt_context_engineering` from Lesson 2. All three of its commonly-cited
macros should work here — unlike the DuckDB project this course started
on, Snowflake's `information_schema` supports the `<database>.
information_schema.tables` pattern `generate_source` depends on, so there
isn't the adapter gap Lesson 2's package hit. Confirm that for real once
the sandbox exists; it's the one claim in this lesson inherited from
before the Snowflake move rather than independently re-verified.

```bash
dbt run-operation generate_source --args '{"schema_name": "raw"}'
dbt run-operation generate_base_model --args '{"source_name": "raw", "table_name": "members"}'
dbt run-operation generate_model_yaml --args '{"model_names": ["stg_members"]}'
```

**Package this as a skill, not three commands to remember.** Three
commands run in the right order, every time a new source shows up, is
exactly the kind of repeatable task a team shouldn't re-explain to an
agent every session —
[`.claude/skills/generate-staging-model/SKILL.md`](../.claude/skills/generate-staging-model/SKILL.md)
wraps all three behind one invocation: given a schema and a table, run
`generate_source` scoped to just that table, then `generate_base_model`,
then `generate_model_yaml`, and stop for review before anything gets
written to disk. It's a markdown file, not a dbt resource (2.4), so
`dbt deps` doesn't install it — it's just committed directly.

## 3.4 — Source Freshness

```bash
dbt freshness
```

`court_reservations` is the one genuinely tight SLA in this project
(`warn_after` 1 day, `error_after` 3 days), because an operational booking
table should need same-day attention if it stops loading; the rest are
deliberately looser (roster and tournament-record tables that get a
routine sync, not a continuous feed). All ten sources were designed to
pass under realistic conditions — see `scripts/generate_demo_data.py`'s
docstring for the `loaded_at` bug this project already found and fixed
once, back when this ran on DuckDB, where a roster table someone joined
years ago read as permanently stale regardless of threshold.

## 3.5 — Key Takeaways

- Treat `sources.yml` as a data contract, not paperwork filed after the fact.
- Generate the mechanical parts (base models, properties YAML) with codegen,
  packaged as a skill so the same three commands don't get re-explained
  every session; don't ask an AI to guess `information_schema` for you.
- Staging does one job. The complexity belongs to the source that earns it,
  not spread evenly across every model out of habit.

## What's next

```bash
git checkout lesson-4-start   # or: lesson-3-end, the same commit
```

Lesson 4 builds the first intermediate models and marts on top of this
staging layer, and converts `stg_court_reservations` into this project's
first incremental model.

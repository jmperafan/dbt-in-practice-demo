# Lesson 1: Setup

**Start:** `git checkout lesson-1-start` · **Finish:** `git checkout lesson-1-end`

## The mental model

Most teams start with a `profiles.yml` on one laptop and credentials in a
file. That works until a second person joins. The half-step that looks
like progress — environment variables documented in a README, a dev/prod
split in `dbt_project.yml`, onboarding as a six-command wiki page — goes
stale the first time the steps change.

The real model a senior engineer builds to is a small number of
non-negotiable decisions, made once, that everything else builds on: which
engine you're running, how credentials are supplied, how many real
environments exist, and how the project itself is laid out. A weak
foundation was always a liability. AI doesn't create that risk — it just
makes the bill for skipping it arrive sooner, because a team of one can now
generate a laptop's worth of models in an afternoon.

## 1.1 — dbt OSS vs. the dbt platform

Two ways to run dbt, and this project deliberately picks one:

- **The dbt platform** is dbt Labs' own managed service: hosted scheduling,
  a browser IDE, environments as a product feature, and the only way to
  get seat-based features like Mesh or Catalog.
- **Self-hosted** is the dbt binary (what this repo uses) run locally or in
  CI, with environments, secrets, and scheduling wired up yourself.

Neither is more "real" dbt — the same project files work on both, and the
platform can run the exact CLI commands this course teaches inside its own
managed jobs. The actual decision: a team that doesn't want to own an
orchestrator, an IDE, and environment provisioning picks the platform; a
team that already has that infrastructure, or wants it in its own stack,
picks self-hosted. This course teaches self-hosted because the patterns
(environments, CI gates, orchestration) transfer either way — they're just
invisible if the platform already handles them for you.

```bash
dbt --version   # confirms which engine you're on
```

## 1.2 — dbt Adapters

An adapter is the plugin that translates dbt's dialect into a given
warehouse's SQL. The install story changed between engines: dbt v1 pins
the adapter as a separate Python package (`pip install dbt-snowflake`); dbt
v2 ships as a standalone binary and resolves an adapter on demand the first
time a profile needs one — nothing to pin in a requirements file. This
project uses DuckDB specifically because dbt Labs documents it as the
easiest way to get a project running locally: no warehouse account, no
credentials, no adapter to install separately.

## 1.3 — Connections and Credentials

DuckDB has no credentials — that's the point for this repo — but the
pattern below is how you'd connect to a real warehouse, and it's worth
knowing even here: a connection block never contains a literal secret.

```yaml
password: "{{ env_var('SF_PASSWORD') }}"
```

In CI, the value comes from a secrets store (GitHub Actions secrets, in
Lesson 8); nothing sensitive ever sits in git history, and rotating a
credential means updating one secret store entry, not hunting through
config files.

## 1.4 — Environments

Three real environments, not three names for the same tables: **dev** (one
schema per developer), **ci** (a schema created fresh per pull request),
**prod** (the actual serving schema). The failure mode this replaces: CI
building directly against a shared "dev" schema, where two pull requests
building at once corrupt each other's state.

[`profiles.yml`](../profiles.yml) defines the three targets. What actually
makes them three *real* environments, not three labels, is
[`macros/generate_schema_name.sql`](../macros/generate_schema_name.sql) —
it turns a model's `+schema: staging` config plus the active target into
`dev_staging`, `ci_pr_123_staging`, or a clean `staging` on prod. One
macro, applied everywhere.

## 1.5 — Git Basics

Nothing dbt-specific here — a branching strategy people actually follow
(this repo uses short-lived feature branches off `main`), and commits that
tell a story:

```bash
git checkout -b feature/stg-reservations
git commit -m "Add stg_court_reservations: normalize mixed time formats"
```

## 1.6 — dbt Project Design

[`dbt_project.yml`](../dbt_project.yml) sets materialization defaults once,
per directory, instead of repeating a `{{ config(...) }}` call in every
file:

- **`staging`** — views. Rename and cast a source's raw columns 1:1,
  nothing else.
- **`intermediate`** — ephemeral. Shared joins and business logic that more
  than one mart needs, inlined rather than materialized, since nothing
  outside this project ever queries it directly.
- **`marts`** — tables. The consumption-ready layer, built out starting in
  Lesson 4.

A model's folder and its prefix (`stg_`, `int_`, `fct_`/`dim_`, once they
exist) always agree, so nobody has to open the file to know what it is.

## What's next

Lesson 1 ends with a working project and nothing to build yet — no
sources, no models. That's deliberate: Lesson 3 is where the raw data
(already loaded into `sutton.duckdb`'s `raw` schema by
`scripts/load_raw_data.py`) gets its first `sources.yml` and its first
staging models.

```bash
git checkout lesson-2-start   # or: lesson-1-end, the same commit
```

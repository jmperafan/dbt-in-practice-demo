# Lesson 8: Deployment

**Start:** `git checkout lesson-8-start` · **Finish:** `git checkout lesson-8-end` (= `main`)

## The mental model

Everything through Lesson 7 made the project correct. This lesson is about
making it *keep* being correct once more than one person (or more than one
agent) is pushing to it at once, without every change requiring a full
rebuild or a human staring at a diff. Deployment is where the project
actually becomes a system, not just a folder of SQL that happens to run.

**Verification status:** checked with `dbt parse`, `dbt compile`, and `dbt
check` against dummy credentials (50 of 52 nodes; the same two
credential-only failures as every prior lesson — `metricflow_time_spine`
and `fct_court_reservations`'s `is_incremental()` check, both needing a
real warehouse connection, not a real error). All three check files pass
exactly as Lesson 7 predicted they would (see 8.6). The GitHub Actions
workflow (8.8) is real, committed YAML, but has not actually run in GitHub
yet — no PR has opened against this repo. Everything needing a dbt
platform account (8.2, 8.3, most of 8.5 and 8.7) is reference, not
something run here — same honesty as every prior lesson's doc-only
sections.

## 8.1 — Core dbt Commands

[`selectors.yml`](../selectors.yml) names one reusable selection,
`ci_slim`, instead of letting the same `state:modified+` string live in
two places (a local terminal and 8.8's CI workflow) and drift apart later:

```bash
dbt ls --select "selector:ci_slim" --state ./prod-artifacts
```

Confirmed by actually running it: with no `--state` given, dbt refuses
cleanly (`Got a state selector method, but no comparison manifest`) rather
than silently selecting everything or nothing — the right failure mode for
a selection method that's only meaningful relative to a prior run's
artifacts.

## 8.2 — dbt Jobs

Doc-only: a dbt Job is a dbt platform object (a saved command, a schedule
or trigger, an environment), not something that exists inside this git
repo at all. The job this project would actually need, once the sandbox
exists: a nightly `dbt build` against the `prod` target (see
[`profiles.yml`](../profiles.yml)), generating the `docs/` site (Lesson 5)
and the `manifest.json` that 8.8's CI workflow fetches as its comparison
state.

## 8.3 — The dbt Platform API

Doc-only, and gated further than 8.2: the Admin API needs a paid Starter
plan, not the free Developer plan this project's own setup doc
([01-setup.md](01-setup.md)) assumes. Worth naming the one thing this API
is actually for, concretely: triggering 8.2's job on demand (a `POST` to
the run-trigger endpoint) instead of waiting for its schedule, and reading
back `run_results.json` (7.3) programmatically instead of through the UI.

## 8.4 — Pre-hooks and Post-hooks

[`fct_court_activity.sql`](../models/marts/fct_court_activity.sql)'s
`post_hook`:

```sql
{{ config(
    post_hook="grant select on {{ this }} to role bi_reader"
) }}
```

A grant, not a side-effect query, on purpose — the one post-hook use case
that's genuinely common in production and genuinely safe to run on every
build: the role a BI tool connects as needs read access re-granted every
time the table's recreated by a `table`-materialized model, since a `grant`
on the old table doesn't carry over to its replacement.

## 8.5 — dbt State

[`dbt_project.yml`](../dbt_project.yml)'s marts config now carries:

```yaml
+state:
  lag_tolerance: 24h
```

The real point of `lag_tolerance`, named honestly rather than left
implicit: it's a tolerance for *this project's own data*, not a dbt
feature that works regardless of what's underneath it. This demo's CSVs
don't change between recordings the way a live production feed would, but
unlike `ztc-core`'s genuinely closed 2022-2023 historical dataset, this
project shouldn't pretend to be permanently static either — 24 hours is a
deliberate middle ground, real tolerance without the dishonesty of
claiming the data never changes. The actual state-comparison machinery
(`--defer --state`) is what 8.8's CI workflow runs for real; `--state
./prod-artifacts` there is the same concept 8.1 just confirmed errors
correctly when it's missing.

## 8.6 — dbt Checks

Three check files, each doing a different job, all confirmed by a real
`dbt check` run against this exact project:

- [`checks/public_models_have_descriptions.sql`](../checks/public_models_have_descriptions.sql) — **passed**
- [`checks/certified_models_meet_the_bar.sql`](../checks/certified_models_meet_the_bar.sql) — **passed**, enforcing for real what Lesson 7.6 only tagged (`meta.certified: true` on [`dim_members`](../models/marts/_dim_members.yml) now actually means owned + contracted, not just claimed)
- [`checks/unused_staging_and_intermediate_models.sql`](../checks/unused_staging_and_intermediate_models.sql) — **warned**, listing exactly four genuinely orphaned staging models (`stg_invoices`, `stg_tournament_entries`, `stg_invoice_line_items`, `stg_tournaments` — the invoicing source data this project loads but has never built a mart on)

[`checks/_checks.yml`](../checks/_checks.yml) sets `severity: warn` on only
the last one — an orphaned staging model might be "not wired up yet," not
broken, so it shouldn't block a build the way a false certification claim
should. The project-wide severity policy Lesson 6.5 asked for and deferred
is this file.

All three run against an embedded DuckDB representation of the project's
own metadata (`info_schema` in [`dbt_project.yml`](../dbt_project.yml)) —
genuinely the one piece of this entire Snowflake-era project that needs no
warehouse connection at all, dummy credentials or not.

## 8.7 — CI Jobs

Doc-only, same gate as 8.3: concurrent CI checks, smart cancellation of a
superseded run, and SQL linting as a CI job all need a paid plan. What's
real and running today either way is 8.8's GitHub Actions workflow — CI
jobs are the dbt-platform-native version of the same idea, not a
prerequisite for it.

## 8.8 — CI/CD with GitHub Actions

[`.github/workflows/dbt-ci.yml`](../.github/workflows/dbt-ci.yml): runs on
every pull request that touches `models/`, `macros/`, `tests/`, `checks/`,
`dbt_project.yml`, or `packages.yml`, installs dbt v2, fetches `main`'s
last known-good `manifest.json`, and runs

```bash
dbt build --select "selector:ci_slim" --defer --state ./prod-artifacts
```

The same Slim CI idea 8.1/8.5 named, as a workflow that actually fires —
only what the PR changed (plus its downstream) gets built fresh; every
unchanged upstream node is deferred to production's last run instead of
rebuilt from scratch. This is real, correct YAML, but it's reference
material here, not a live workflow: GitHub Actions only ever discovers
`.github/workflows/` at a repository's actual root, and `lesson-8-deployment/`
is a folder nested inside this repo, not a GitHub repo of its own. Treat this
file the way you'd treat any other lesson file: copy it to your own
repo's actual root to run it for real. The `manifest.json` fetch step
would also still need a `prod-manifest/` path on `main`, which 8.2's dbt
Job (once it exists) is the thing that would populate it.

**No new AI guardrail in this lesson, on purpose.** Every other lesson
since Lesson 2 added a skill, a hook, or an extension to one — the point
being made by this lesson's absence of one is as deliberate as the others'
presence: deployment's job is enforcing what the project already is
(8.6's checks, 8.8's CI selection), not generating anything new, so there's
no natural seam for a guardrail here. Forcing one in anyway would be the
opposite of what every other lesson's guardrail was actually for.

## Where this leaves the project

Eight lessons in, this is no longer a tutorial project: it has sources
with freshness contracts, tested and documented marts, an enforced schema
contract on its one externally-consumed dimension, a real governance
policy backed by an actual check instead of just a tag, and a CI workflow
that only rebuilds what changed. Every guardrail added along the way,
`check_no_select_star.py`, `generate-staging-model`, `draft-column-descriptions`,
the extended `model-reviewer` subagent, `check_naming_convention.py`, and
`AGENTS.md` itself, is still active in `.claude/settings.json` right now,
not retired once its own lesson ended. That's the actual throughline of
this course: none of this is a phase you finish and move past. It's the
shape a dbt project has to take once AI is writing most of the SQL in it,
applied here one real decision at a time instead of asserted in the
abstract.

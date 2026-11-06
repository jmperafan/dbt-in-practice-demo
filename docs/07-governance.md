# Lesson 7: Governance

**Start:** `git checkout lesson-7-start` · **Finish:** `git checkout lesson-7-end`

## The mental model

Nobody assigns a data team an external governance committee, and even the
ones that exist rarely know the data well enough to give more than generic
guidance. In practice, you're the default enforcer and enabler of
governance whether you signed up for that or not — and now that AI is
writing most of the SQL, a governance gap turns into a real problem faster
than it used to, since there's more to govern per unit of time than ever.

**Verification status:** checked with `dbt parse` and `dbt compile`
against dummy credentials (50 of 52 nodes; the same two credential-only
failures as the last three lessons — full contract *enforcement* against
real built columns is one of the two things genuinely unconfirmed until
the sandbox exists).

## 7.1 — Ownership

Already real as of Lesson 5: every mart's `meta.owner` (see any
`models/marts/_*.yml`). This lesson is where it starts getting used for
something — 7.4's audit trail and 7.5's clean-up both key off it.

## 7.2 — Model Contracts

[`_dim_members.yml`](../models/marts/_dim_members.yml) is this project's
first contract: `contract: {enforced: true}`, every column's `name` and
`data_type` declared. `dim_members` specifically, not a fact table, since
a dimension's shape is the one most likely to have real external
consumers (a BI tool, this lesson's own certification tag) who'd be
broken silently by an unannounced schema change.

## 7.3 — dbt Artifacts

Every invocation writes `manifest.json` (the full project graph),
`run_results.json` (what ran, pass/fail, timing), and `catalog.json` to
`target/` — the same files `dbt parse`/`dbt compile` have been producing
throughout this build, read back for this doc's own compile-check
summaries (`52 total | 50 success`). Worth ingesting into the warehouse
(the `dbt_artifacts` package, not added to this project) instead of
letting the next run's artifacts overwrite them — "how long did this
model take last Tuesday" is a query against history then, not a question
nobody can answer.

## 7.4 — Audit Logging

Doc-only for this project, genuinely: a real audit trail (warehouse query
history, dbt run logs, access-grant history, often shipped to a SIEM)
needs a live Snowflake account to mean anything, not a demo project. The
one thing worth naming now: "who ran what, when" increasingly means an
agent session, not just a person — `.claude/settings.json`'s hooks are
already a local version of exactly that, a record of what ran
automatically, just not centralized anywhere yet.

## 7.5 — Project Clean-Up

```bash
dbt ls --select "models/marts/+"
```

Deliberately not a dbt Check here — Checks are genuinely Lesson 8's own
content (8.6), not borrowed early the way `member_feedback` was borrowed
into Lesson 2. `dbt ls` is the plain-CLI sanity check available right now:
confirm every mart actually has something downstream (or is meant not to),
without the project-metadata-query tooling Lesson 8 introduces properly.

## 7.6 — Model Certification

[`_dim_members.yml`](../models/marts/_dim_members.yml)'s
`meta.certified: true` is a convention, not a dbt feature — the tag alone
proves nothing. The real bar, named explicitly rather than left implicit:
an owner, an enforced contract, real test coverage, real descriptions.
`dim_members` is the one model in this project that actually clears all
four right now, which is why it's the one carrying the tag. Lesson 8's
`checks/certified_models_meet_the_bar.sql` is what turns "clears the bar"
from a claim into something enforced — not built yet, on purpose, same
sequencing reason as 7.5.

## 7.7 — dbt Mesh

[`models/_groups.yml`](../models/_groups.yml) defines one group,
`analytics_engineering`, applied to the whole marts layer in
[`dbt_project.yml`](../dbt_project.yml). One group, not one per domain,
and no second project, is the actual conclusion this lesson reaches for
this specific project, not a shortcut taken to save build time.

dbt Labs' own mesh-fit guidance is organizational structure, not model
count: an enterprise mesh is warranted around a domain-team-to-platform-
team ratio of roughly 10:1 or higher; hub-and-spoke fits around 5:1; a
single team owning the whole DAG end to end is dbt Labs' own "single-team
monolith" case, where mesh "may not be required," regardless of how large
the project gets. This project is one person's demo — the ratio is
undefined, or at best 1:1 — so the honest application of the real
framework is: no mesh, no cross-project `ref()`, one group. Credibility
comes from applying the framework and landing where it actually points,
not from building the advanced pattern because the lesson exists.

**The guardrail for this lesson, the biggest one so far:**
[`AGENTS.md`](../AGENTS.md) at the repo root — the concrete version of
every convention this project has accumulated since Lesson 1, written so
an agent doesn't have to re-derive any of it from scratch each session.
Paired with enforcement, not just a document: `.claude/settings.json` now
also runs
[`scripts/check_naming_convention.py`](../scripts/check_naming_convention.py),
a `PreToolUse` hook blocking a new model file that doesn't match its
layer's prefix (`stg_`, `int_`, `dim_`/`fct_`) before it's ever written —
tested directly against five cases (a bad new file, a correct new file, a
properties YAML, a correctly-named staging file, and an edit to an
existing file), all five behave correctly.

## What's next

```bash
git checkout lesson-8-start   # or: lesson-7-end, the same commit
```

Lesson 8 is where this project actually ships: core commands, dbt Jobs,
the platform API, pre/post-hooks, dbt State, dbt Checks (7.5 and 7.6's
promised enforcement), CI jobs, and CI/CD with GitHub Actions.

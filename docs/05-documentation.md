# Lesson 5: Documentation

**Start:** `git checkout lesson-5-start` · **Finish:** `git checkout lesson-5-end`

## The mental model

Most teams write one kind of documentation and call it done. Per
Diátaxis (Daniele Procida's framework, the same one Django and Canonical's
own docs use): **tutorials**, **how-to guides**, **reference**, and
**explanation** are four different needs. A dbt model's generated column
and model descriptions are reference, full stop — information consulted
while working, not a place to explain or instruct. This lesson is honest
about that limit: it teaches reference well (automatable, demoable) and
one how-to (ownership tied to on-call); explanation and tutorial are real
needs this project doesn't cover.

**Verification status:** checked with `dbt parse` and `dbt compile`
against dummy credentials. One real, substantive finding this lesson
surfaced: the Semantic Layer YAML I first wrote (5.5) was the *deprecated*
legacy shape. `dbt parse` said so directly (`SemanticModelDeprecated`),
and the fix — semantic config embedded in the model's own properties file,
entities/dimensions at the column level — is documented below as what
actually works on dbt v2, not the shape most existing tutorials still show.

## 5.1 — The dbt Catalog

[`models/marts/_dim_members.yml`](../models/marts/_dim_members.yml) and its
three sibling files are this project's first real `description:` fields
beyond a bare sentence — dbt's own documentation primitive, compiled into
whatever `dbt docs generate` / `dbt docs serve` builds.

## 5.2 — Tags and Meta Tags

Every mart now carries `tags:` (`dimension`, `fact`, `incremental`) and
`meta: {owner: ...}` — see any `_*.yml` under `models/marts/`. `dbt build
--select tag:fact` runs just the two fact tables; the owner tag is what
Lesson 7's audit logging and failure-routing actually key off later.

## 5.3 — Doc Blocks

[`models/docs.md`](../models/docs.md) has two: `member_id` and
`court_number`, the two columns repeated across the most models in this
project. `member_id`'s doc block is where the `GHOST-` quirk (Lesson 3,
Lesson 6) gets explained once, referenced everywhere, instead of
re-explained — or silently left unexplained — in every model that happens
to carry a `member_id` column.

## 5.4 — YAML Management

One file per model (`_dim_members.yml`, `_dim_coaches.yml`,
`_fct_court_reservations.yml`, `_fct_court_activity.yml`), not one
`_marts__models.yml` covering all four — this project's marts layer
started as a single combined file in Lesson 4 and was deliberately split
here, so two people working on different marts never collide on the same
file's merge.

**The guardrail for this lesson:**
[`.claude/skills/draft-column-descriptions`](../.claude/skills/draft-column-descriptions/SKILL.md)
drafts descriptions for a model's undocumented columns from its compiled
SQL and any upstream doc block, then stops before writing anything —
review is spot-checked by criticality (a column already in a doc block or
a certified model gets a real read, an internal low-traffic column gets a
lighter pass), never shipped unread just because an agent drafted it fast.

## 5.5 — Semantic Layer

[`models/marts/_fct_court_activity.yml`](../models/marts/_fct_court_activity.yml)
defines one metric, `court_hours_used`, and
[`models/metrics/metricflow_time_spine.sql`](../models/metrics/metricflow_time_spine.sql)
is the time-spine model the Semantic Layer expects to exist, built with
`dbt_utils.date_spine` (already installed, Lesson 4).

**What actually changed, confirmed by running `dbt parse` and reading the
warning, not by guessing:** dbt v2 deprecated the old top-level
`semantic_models:` block. The current shape lives inside the model's own
properties file:

```yaml
models:
  - name: fct_court_activity
    semantic_model:
      enabled: true
      name: court_activity
    agg_time_dimension: activity_date
    columns:
      - name: court_activity_id
        entity: {type: primary, name: court_activity}
      - name: activity_date
        dimension: {type: time}
    metrics:
      - name: court_hours_used
        type: simple
        agg: sum
        expr: duration_hours
```

Entities and dimensions are annotated at the column level, inside the same
file Lesson 5.1-5.4 already uses for descriptions, tags, and tests — one
fewer place to keep in sync, not a separate `semantic_models:` file most
existing tutorials (including this project's own early draft) still show.
Documenting for a human reader (5.1's descriptions) and documenting so a
BI tool or an agent gets a governed number (this metric) are different
jobs, living in the same file on purpose.

## What's next

```bash
git checkout lesson-6-start   # or: lesson-5-end, the same commit
```

Lesson 6 tests this project's growing mart layer: which of the generic,
singular, and unit test types fits a given risk, and why staging already
got the heaviest coverage back in Lesson 3.

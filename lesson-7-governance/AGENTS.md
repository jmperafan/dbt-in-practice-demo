# Topspin Tennis Academy — agent conventions

Any coding agent working in this repo reads this file automatically. It's
the concrete version of this project's conventions — not "follow best
practices," but the exact rule an agent (or a person) needs to follow it
without re-deriving it from scratch every session.

## Layers and naming

- **`models/staging/`** — `stg_<source_table>.sql`, materialized `view`.
  Rename and cast a source's raw columns 1:1. Never drop a row or a
  column, never add business logic.
- **`models/intermediate/`** — `int_<description>.sql`, materialized
  `ephemeral`. Shared joins/business logic more than one mart needs.
  Nothing outside this project queries these directly.
- **`models/marts/`** — `dim_<entity>.sql` / `fct_<entity>.sql`,
  materialized `table` (or `incremental`, set explicitly in the model
  file, not the project default, when a model's own volume earns it — see
  `fct_court_reservations.sql`).
- **`models/context/`** — `int_<source>_embeddings.sql`, materialized
  `table`. What an AI agent reads, not what a person reads — see
  `../lesson-2-ai-infrastructure/README.md` (2.3) before adding to this layer.
- **`models/metrics/`** — Semantic Layer config, embedded in the relevant
  mart's own `_<model>.yml` (dbt v2 shape), not a separate
  `semantic_models:` file. `metricflow_time_spine.sql` lives here too.

## Before a model is considered done

1. `dbt parse --project-dir . --profiles-dir .` compiles clean. Enforced
   automatically — see `.claude/settings.json`'s `PostToolUse` hook.
2. No `select *` in any `.sql` file. Enforced automatically — see
   `.claude/settings.json`'s `PreToolUse` hook
   (`scripts/check_no_select_star.py`).
3. Test coverage matches the layer: a staging primary key gets
   `unique`/`not_null`; a mart's foreign key to another mart gets a
   `relationships` test, with `severity: warn` only for a known, already-
   accepted gap (document why, like `_fct_court_reservations.yml` does for
   `GHOST-` ids) — anything else is a hard error. Model logic with a
   conditional or a cast worth getting wrong (see
   `stg_court_reservations`) gets a unit test against fixtures.
4. One properties YAML per model (`_<model_name>.yml`), never a combined
   file covering several models — see `../lesson-5-documentation/README.md` (5.4)
   for why.
5. A column repeated across several models' descriptions (`member_id`,
   `court_number`) uses the doc block in `models/docs.md`, not a
   re-written description in each file.

## Checking this yourself

[`.claude/agents/model-reviewer.md`](.claude/agents/model-reviewer.md) is
a subagent that checks points 1-4 above for a model you just changed, and
reports pass/fail without fixing anything itself.
[`.claude/skills/generate-staging-model`](.claude/skills/generate-staging-model/SKILL.md)
and
[`.claude/skills/draft-column-descriptions`](.claude/skills/draft-column-descriptions/SKILL.md)
are the two repeatable tasks this project has packaged as skills so far —
check whether one already covers what you're about to do by hand.

## What this project is not

One team owns this whole DAG. That makes it a single-team monolith by dbt
Labs' own mesh-fit framework (organizational ratio, not model count — see
`README.md`), so there's one `+group` for the whole marts
layer (`models/_groups.yml`), not one per domain. Don't propose splitting
this project or adding more groups without that ratio actually changing
first.

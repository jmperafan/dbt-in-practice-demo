# Lesson 2: AI Infrastructure

**Start:** `git checkout lesson-2-start` · **Finish:** `git checkout lesson-2-end`

## The mental model

Every AI segment later in this course, Sources' staging-model generation,
Development's validation tiers, Governance's agent-navigable structure,
depends on one access layer and one context discipline. Teaching that
infrastructure here, first, means those later lessons build on established
vocabulary instead of each one defining MCP or a skill from scratch.

Most of this lesson's content lives in how you configure your coding agent,
not in dbt resources, so this lesson's repo changes look different from
Lesson 1's: a couple of `.claude/` files instead of `.sql`/`.yml`.

## 2.1 — Using dbt Wizard

dbt Wizard works from the project's own metadata, a current
`target/manifest.json`, not by guessing from code alone, and has you choose
an explicit validation level before it acts:

| Level | What it checks | Use it when |
|---|---|---|
| Light | Syntax, lint, focused tests, no materialization | Low-risk change, need fast feedback |
| Medium (default) | + compiles, materializes modified models in dev | Changed model logic |
| Heavy | + dev/prod comparison: row counts, schema diffs | Grain/financial/contract-level change |
| Skip | No structured validation | Draft only |

Before letting it edit anything, ask it to scope the change first:

```text
Review my uncommitted changes. Explain which dbt resources changed, trace
their downstream impact, and propose a validation plan. Do not edit yet.
```

## 2.2 — The Anatomy of a Good Prompt

Structure every request the same way so nothing gets assumed: **role**
(senior analytics engineer on this project), **context** (which model, what
must stay true), **task** (the specific change, named), **format** (where
the output goes), **constraints** (dialect, fixtures, no warehouse cost for
a draft). The structure itself isn't the skill, the validation-level
decision in 2.1 is.

## 2.3 — Context Engineering

**Real and runnable here now** — this is the segment that drove the move
off DuckDB. dbt Labs ships
[`dbt_context_engineering`](https://github.com/dbt-labs/dbt-context-engineering),
an open-source package for modeling unstructured text (call transcripts,
support tickets, feedback) as dbt objects an agent can retrieve by meaning
and cite. Verified directly against the package's own source (0.2.0): its
`embed()`/`generate()`/`classify()`/`extract()` functions only have real
implementations for **Snowflake (Cortex), Databricks, BigQuery, and
Redshift (Bedrock)** — anything else, including DuckDB, hits a deliberate,
named compiler error rather than failing silently. That's the one line
this package's own move didn't change: it still won't run on DuckDB, this
project just isn't on DuckDB anymore.

The usual pattern is chunk → embed → search, three models. This project's
`member_feedback` table (Lesson 3) skips chunk: each comment is already one
short, complete thought, not a transcript with many turns that need
packing into token-bounded pieces first. `embed()` works directly on text
that's already atomic — the package's own docs confirm the three steps are
independently useful, not a fixed pipeline. Chunk still matters for
anything longer; see the package's README for that macro's signature.

[`models/context/int_member_feedback_embeddings.sql`](../models/context/int_member_feedback_embeddings.sql)
is the real model:

```sql
select
    feedback_id,
    member_id,
    category,
    comment_text,
    submitted_date,
    {{ dbt_context_engineering.embed('comment_text') }} as embedding
from {{ ref('stg_member_feedback') }}
```

Two things the package requires before this will actually run, both set in
[`dbt_project.yml`](../dbt_project.yml):

- **`vars: {ai_functions_enabled: true}`** — off by default, on purpose,
  so a fresh or CI target never triggers a real, billed AI call just by
  running `dbt build`. Compared as a literal `"true"`/`"false"` string, not
  Jinja truthiness (the package's own docs name a specific way a
  conditional expression here silently does the wrong thing), so it's set
  plainly rather than per-target.
- **`vars: {embedding_model: ...}`** — which Cortex embedding model your
  Snowflake account/region actually has enabled. Still a placeholder here;
  fill it in once the sandbox exists.

Search, the third step, is inherently ad hoc (the query changes every time
someone asks something), so it isn't a committed model here, just the real
macro call to run once there's a corpus to search:

```sql
{{ dbt_context_engineering.vector_search(
    relation=ref('int_member_feedback_embeddings'),
    embedding_column='embedding',
    query_embedding=dbt_context_engineering.embed('late cancellations and refund complaints')
) }}
```

**One more thing worth knowing, found while setting this up, not
documented anywhere obvious:** this package ships its own agent skills
(`dbt-ce-setup`, `dbt-ce-ai-functions`, `dbt-ce-pipeline`), and dbt v2
installs them straight from `dbt deps` into `.claude/skills/`, once
`flags: {ai_provider: claude}` is set in `dbt_project.yml`. That's a
different, newer mechanism than 2.4's marketplace install below, a package
carrying its own skills along for the ride, and it's easy to miss since
`dbt deps` only warns, it doesn't fail, if `ai_provider` isn't set.

## 2.4 — AI Skills

A skill is a markdown file, not a dbt resource. The usual way a team adds
one is explicit and manual, installing into the agent itself, not through
`packages.yml`:

```bash
/plugin marketplace add dbt-labs/dbt-agent-skills
/plugin install dbt@dbt-agent-marketplace
```

dbt Labs' own repo covers analytics engineering, Semantic Layer work,
platform operations, and the dbt v1→v2 migration. MCP (2.5) is how an agent
gets access to tools; skills are how it gets the knowledge to use them well.

**The exception, found building 2.3, not something either package's own
README states plainly:** a dbt package can bundle its own skills and have
`dbt deps` install them automatically, if `flags: {ai_provider: claude}` is
set — see `dbt_context_engineering`'s three skills, installed that way in
this very project. Marketplace install is a team choosing to add
conventions; a package bundling its own skills is the package author
teaching an agent how to use that specific package correctly. Different
intent, same underlying skill format.

## 2.5 — The dbt MCP Server

The dbt MCP server is a read-only layer over dbt's own APIs and local
commands, not a file reader over `manifest.json`. It ships self-hosted
(`uvx dbt-mcp`, full command access, works with or without a dbt platform
account) or remote (HTTP, dbt-platform-hosted, consumption only, no local
dbt commands). This project uses self-hosted: day-to-day dbt runs stay
local even though the project is also bound to a dbt platform project
(1.1), and self-hosted is the only mode that can actually run a command
against this repo, not just query metadata about it.

It isn't a static file you commit, since `DBT_PROJECT_DIR` and `DBT_PATH`
are specific to your own machine. Point your agent at this project with:

```bash
claude mcp add dbt \
  -e DBT_PROJECT_DIR=/absolute/path/to/this/repo \
  -e DBT_PATH="$(which dbt)" \
  -- uvx dbt-mcp
```

Demo it live: ask an agent something about this project's lineage with and
without that connection, and compare what it can answer.

## 2.6 — Hooks

A hook is a shell command the agent's own harness runs automatically, not
something the agent decides to do. [`.claude/settings.json`](../.claude/settings.json)
in this repo runs `dbt parse` after every file write or edit:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "dbt parse --project-dir . --profiles-dir . --quiet || true"}]
      }
    ]
  }
}
```

A broken `ref()` or a Jinja typo gets caught the moment a file is saved, not
whenever someone next remembers to run `dbt parse` by hand.

## 2.7 — Agents

A single agent on a large, multi-step task tends to lose track of its own
earlier decisions as its context window fills up. The alternative: split
the work across specialized subagents, a planner that breaks the task into
pieces, a generator that does the work on each piece with a clean context
window, and an evaluator that checks the generator's output before it's
accepted.
[`.claude/agents/model-reviewer.md`](../.claude/agents/model-reviewer.md)
in this repo is that evaluator: it checks that a changed model compiles,
sits in the right layer, carries the test coverage its layer calls for, and
is named correctly, then reports pass/fail without fixing anything itself.

This is Situational, not a default: most of what this course teaches runs
through one agent at a time. Reach for a subagent split once a task has
actually outgrown that.

## What's next

```bash
git checkout lesson-3-start   # or: lesson-2-end, the same commit
```

Lesson 3 is where this project's first real source lands, `sources.yml`
against the `raw` schema `scripts/load_raw_data.py` already populated, and
the first staging models get built.

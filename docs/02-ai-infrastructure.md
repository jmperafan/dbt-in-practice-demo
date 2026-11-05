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

**Verified, real, and genuinely useful, but not runnable on this project.**
dbt Labs ships [`dbt_context_engineering`](https://github.com/dbt-labs/dbt-context-engineering),
an open-source package for modeling unstructured text (call transcripts,
support tickets, contracts) as dbt objects an agent can retrieve by meaning
and cite. Its pattern is chunk, then embed, then search:

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_context_engineering
    version: 0.1.0
```

```sql
{{ dbt_context_engineering.chunk(
    relation = ref('stg_member_feedback'), id_column = 'feedback_id',
    order_column = 'sentence_index', text_column = 'comment_text',
    partition_column = 'member_id'
) }}
```

The catch for this project specifically: the package is built and validated
against **Snowflake (Cortex), Databricks, BigQuery, and Redshift (Amazon
Bedrock)** only. DuckDB isn't one of the four, so this isn't added to this
repo's own `packages.yml`, there's nothing here it could embed against. If
your own project runs on one of those four, this is the real install and the
real macro call, not a simplified version.

## 2.4 — AI Skills

A skill is a markdown file, not a dbt resource, so it doesn't travel through
`packages.yml`/`dbt deps`. It installs into the agent itself:

```bash
/plugin marketplace add dbt-labs/dbt-agent-skills
/plugin install dbt@dbt-agent-marketplace
```

dbt Labs' own repo covers analytics engineering, Semantic Layer work,
platform operations, and the dbt v1→v2 migration. MCP (2.5) is how an agent
gets access to tools; skills are how it gets the knowledge to use them well.

## 2.5 — The dbt MCP Server

The dbt MCP server is a read-only layer over dbt's own APIs and local
commands, not a file reader over `manifest.json`. It ships self-hosted
(`uvx dbt-mcp`, full command access, no warehouse account needed) or remote
(HTTP, dbt-platform-hosted, consumption only). This project uses
self-hosted, since everything here already runs without a platform account.

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

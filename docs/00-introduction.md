# Introduction

**Start here:** `git checkout lesson-1-start`

## Why this course, why this repo

In the past, if you wanted more output from a data team, you had two
options: hire more people, or get better at the tool. That's not really
true anymore. A small team using AI can produce the SQL volume that used to
take twenty people. Output isn't the constraint. The real question has
changed from "how do we produce more" to "how do we produce better," and
that's a governance problem, not a tooling one.

*dbt in Practice* is built around that shift. It doesn't teach dbt syntax —
there are great courses for that already (start at
[learn.getdbt.com](https://learn.getdbt.com) if you need one first). It
teaches the decisions a senior practitioner makes once a project has to
survive more than one contributor, more than one environment, and a
teammate that happens to be an AI agent.

This repo is where that gets built, for real, lesson by lesson, against a
fictional tennis academy called Topspin. Nothing in it is a toy that gets
thrown away at the end of the lesson — the project you build in Lesson 1 is
the exact project Lesson 8 ships.

## How the course is laid out

1. **Setup** — getting a project built the right way, before a second
   contributor (human or AI) joins.
2. **AI Infrastructure** — treated early and once, on purpose: the
   vocabulary (MCP, skills, hooks, context engineering) every later lesson
   assumes instead of re-explaining.
3. **Sources** — treating raw data as a contract, not an assumption.
4. **Development** — managing the complexity that's left once AI is
   writing most of the SQL.
5. **Documentation** — keeping it honest and current at a volume no human
   maintains by hand.
6. **Testing** — investing proportional to where data actually enters your
   control, not a flat percentage everywhere.
7. **Governance** — ownership, contracts, and enforcement that doesn't
   depend on anyone reading a wiki page.
8. **Deployment** — running this safely in production, with or without a
   managed platform.

## Before you start

This assumes you already know dbt: models, `ref()`, basic tests, the
mental model of a DAG. If any of that is new, the fundamentals course at
learn.getdbt.com is the right place to pick it up — come back once it's
second nature.

You'll need dbt v2 and the DuckDB CLI, nothing else. See
[01-setup.md](01-setup.md) for both, and for why this project runs on
DuckDB instead of a cloud warehouse.

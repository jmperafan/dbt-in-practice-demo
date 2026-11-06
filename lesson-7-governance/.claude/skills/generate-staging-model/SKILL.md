---
name: generate-staging-model
description: Scaffold a new source and its staging model from an existing raw table, using dbt-labs/codegen. Use when a new table has landed in the raw schema and needs a sources.yml entry, a staging model, and a properties file.
---

Given a schema name and a table name, scaffold the three artifacts every
new source in this project needs, in this order:

1. `dbt run-operation generate_source --args '{"schema_name": "<schema>", "table_names": ["<table>"]}'`
   Introspects the warehouse, produces a `sources.yml` entry. Add it to
   `models/staging/_raw__sources.yml`, not a new file — every source in
   this project lives in that one file.
2. `dbt run-operation generate_base_model --args '{"source_name": "<schema>", "table_name": "<table>"}'`
   Produces the staging model SQL: a rename/cast skeleton, one column per
   line, nothing else.
3. `dbt run-operation generate_model_yaml --args '{"model_names": ["stg_<table>"]}'`
   Produces that staging model's properties YAML.

**Stop after generating. Do not write any of the three to disk yet.**
Show the generated YAML and SQL, then:

- Review and rename columns that need it (the raw column name is rarely
  the right staging name verbatim).
- Add a real `description:` to the source, every column with PII, and the
  model itself — the generated ones are empty placeholders, not drafts
  worth shipping.
- Add any `data_tests` the primary key needs (`unique`, `not_null`) and a
  `freshness` block matching this source's actual update cadence — see
  the existing entries in `_raw__sources.yml` for realistic examples
  (roster tables: loose; `court_reservations`: tight).
- Only then write the files, following this project's existing staging
  model style (see any `stg_*.sql` for the pattern).

This mirrors Lesson 3's own `generate_source`/`generate_base_model`/
`generate_model_yaml` sequence exactly — the only difference is not
re-explaining the three-command order and the review step every time a
new table shows up.

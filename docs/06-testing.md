# Lesson 6: Testing

**Start:** `git checkout lesson-6-start` · **Finish:** `git checkout lesson-6-end`

## The mental model

Investment proportional to where data actually enters your control, not a
flat percentage applied everywhere out of habit. Staging already got the
heaviest coverage, back in Lesson 3 (every primary key: `unique` and
`not_null`) — that's the layer every downstream model inherits from, so a
problem caught there is caught once. This lesson is about the marts layer,
where the risk is different: business logic, cross-model relationships,
and known, already-accepted data-quality gaps that need a different kind
of test than a staging model does.

**Verification status:** checked with `dbt parse` and `dbt compile`
against dummy credentials (50 of 52 nodes; the same two credential-only
failures as Lessons 4-5). Two real, substantive corrections this lesson
surfaced, both from actually running `dbt deps`/`dbt parse` rather than
trusting remembered syntax — see 6.3 and 6.4.

## 6.1 — Singular Data Tests

[`tests/assert_no_negative_duration_hours.sql`](../tests/assert_no_negative_duration_hours.sql):
a business rule too specific for a generic test — no activity on a court
should ever have a negative duration, regardless of which of the three
source tables in `fct_court_activity` it came from.

## 6.2 — Generic Data Tests

[`_fct_court_reservations.yml`](../models/marts/_fct_court_reservations.yml)
adds `accepted_values` on `status` and `booking_type`, and a
`relationships` test on `member_id` (6.2's taxonomy, used correctly: a
generic, reusable test for a reusable shape of problem, not a one-off).

**Real correction found by running `dbt parse`, not assumed:** dbt v2
requires every generic test's arguments nested under an `arguments:` key
now — `accepted_values: {values: [...]}` at the top level is deprecated
and errors outright (`DbtYamlValidationError`). The fix is
`accepted_values: {arguments: {values: [...]}}`; see any test in this
lesson's YAML for the current shape.

## 6.3 — Unit Tests

[`models/staging/_stg_court_reservations.yml`](../models/staging/_stg_court_reservations.yml):
a unit test against fixtures, not real data, for the one piece of
*logic* in this project worth getting wrong silently —
`stg_court_reservations`'s mixed-timestamp normalization (Lesson 3.2). A
data test can only tell you today's real rows happen to look right; this
test proves the `CASE` logic itself handles both the bare `"HH:MM"` and
the full-timestamp format correctly, before it ever runs against a real
row.

## 6.4 — Advanced Testing with dbt Packages

[`_fct_court_activity.yml`](../models/marts/_fct_court_activity.yml) adds
`dbt_expectations.expect_column_values_to_be_between` on `duration_hours`
— a richer assertion than a hand-written singular test, in one line
instead of a second `tests/*.sql` file.

**Real correction, found the same way as 6.2:** `calogica/dbt_expectations`,
the package name in wide circulation, has moved — `dbt deps` reported
`PackageRedirectDeprecation` and named the new home directly,
`metaplane/dbt_expectations`. [`packages.yml`](../packages.yml) uses the
current name.

## 6.5 — Test Coverage

Not a flat percentage: `member_id`'s `relationships` test is
`severity: warn`, not a hard error, because the `GHOST-` rows it genuinely
catches (the same doc block from Lesson 5) are a known, accepted-for-now
issue, not a broken build — blocking `dbt build` on every run over
something already understood would just train everyone to ignore the test
entirely. `status` and `booking_type`'s `accepted_values` tests are plain
errors, because an unrecognized value there is new and worth stopping for.
Enforcing that distinction consistently, project-wide, by a rule rather
than a case-by-case judgment call, is Lesson 8's dbt Checks — not
introduced here on purpose, since Checks are genuinely that lesson's own
content, not this one's.

**The guardrail for this lesson:** extended, not new —
[`.claude/agents/model-reviewer.md`](../.claude/agents/model-reviewer.md)'s
test-coverage check (added in Lesson 2) now names the actual rule: a
staging primary key needs `unique`/`not_null`, a mart's foreign key needs
a `relationships` test with the severity decided on purpose (not
defaulted), and model logic worth getting wrong gets a unit test, not just
a data test.

## What's next

```bash
git checkout lesson-7-start   # or: lesson-6-end, the same commit
```

Lesson 7 is where ownership, contracts, and an audit trail turn this
project from "it works" into "it's trustworthy" — including a project
clean-up check and a real `dbt Mesh` decision for this specific project's
org structure.

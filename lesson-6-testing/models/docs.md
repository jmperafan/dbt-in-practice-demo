{% docs member_id %}
The member this row belongs to. Resolves to `dim_members.member_id` for a
real member. A small share of rows across this project resolve to a
`GHOST-####` id instead, matching no real member (a deleted record or a
data-entry error at the source) — see the relevant source's own
description in `models/staging/_raw__sources.yml` for that table's exact
rate, and Lesson 6 for the relationships test that catches it.
{% enddocs %}

{% docs court_number %}
Which of this academy's courts (1 through 6) the row refers to. Not a
foreign key to a `dim_courts` table — this project has no court dimension,
since nothing beyond the number itself (no court-level attributes like
surface type) is tracked yet.
{% enddocs %}

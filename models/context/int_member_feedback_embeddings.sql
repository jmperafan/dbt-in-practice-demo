-- Each feedback comment is already a short, complete thought, one row, one
-- idea — unlike a call transcript (many turns that need packing into
-- token-bounded chunks before embedding), there's nothing to chunk here.
-- dbt_context_engineering's own docs confirm chunk and embed are
-- independently useful: embed() works directly on text that's already
-- atomic. See docs/02-ai-infrastructure.md (2.3) for when chunking would
-- actually be needed.

select
    feedback_id,
    member_id,
    category,
    comment_text,
    submitted_date,
    {{ dbt_context_engineering.embed('comment_text') }} as embedding
from {{ ref('stg_member_feedback') }}

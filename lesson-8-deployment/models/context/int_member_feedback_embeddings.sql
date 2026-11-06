-- Each feedback comment is already a short, complete thought, one row, one
-- idea — unlike a call transcript (many turns that need packing into
-- token-bounded chunks before embedding), there's nothing to chunk here.
-- dbt_context_engineering's own docs confirm chunk and embed are
-- independently useful: embed() works directly on text that's already
-- atomic. See ../lesson-2-ai-infrastructure/README.md (2.3) for when chunking would
-- actually be needed.

-- Incremental and version-aware (the package's own ADR-0004 pattern), not
-- the table-every-run shape this model started as: content_hash is the
-- "did this comment's text change" half of the cache key, and
-- embedding_fn_fingerprint (compiled into model_version, fed through
-- incremental_delta_predicate) is the "did embedding_model itself change"
-- half — a model swap re-embeds everything, a routine run re-embeds only
-- new or edited comments. full_refresh is gated behind a var so an
-- unrelated --full-refresh on a shared job can't silently re-bill the
-- whole corpus. guard_batch/log_ai_run scope to that same delta (the only
-- thing this run is actually about to spend on); complete_ai_run closes
-- out the run log entry log_ai_run opened.
{{ config(
    materialized='incremental',
    unique_key='feedback_id',
    full_refresh=var('allow_full_reembed', false),
    pre_hook=[
        "{{ dbt_context_engineering.guard_batch(
            relation=this, input_column='comment_text',
            filter=dbt_context_engineering.incremental_delta_predicate(
                'feedback_id',
                version=dbt_context_engineering.embedding_fn_fingerprint(),
                content_hash_column='content_hash')) }}",
        "{{ dbt_context_engineering.log_ai_run('embed', relation=this, input_column='comment_text',
            filter=dbt_context_engineering.incremental_delta_predicate(
                'feedback_id',
                version=dbt_context_engineering.embedding_fn_fingerprint(),
                content_hash_column='content_hash')) }}"
    ],
    post_hook="{{ dbt_context_engineering.complete_ai_run('embed') }}"
) }}

with source as (

    select
        feedback_id,
        member_id,
        category,
        comment_text,
        submitted_date,
        {{ dbt_context_engineering.content_hash('comment_text') }} as content_hash
    from {{ ref('stg_member_feedback') }}

)

select
    feedback_id,
    member_id,
    category,
    comment_text,
    submitted_date,
    content_hash,
    '{{ dbt_context_engineering.embedding_fn_fingerprint() }}' as model_version,
    {{ dbt_context_engineering.embed('comment_text') }} as embedding
from source
{% if is_incremental() %}
where {{ dbt_context_engineering.incremental_delta_predicate(
    'feedback_id',
    version=dbt_context_engineering.embedding_fn_fingerprint(),
    content_hash_column='content_hash') }}
{% endif %}

{{ config(
    post_hook="grant select on {{ this }} to role bi_reader"
) }}

select
    {{ dbt_utils.generate_surrogate_key(['court_number', 'activity_date', 'started_at', 'activity_type', 'source_id']) }} as court_activity_id,
    court_number,
    activity_date,
    started_at,
    duration_hours,
    activity_type,
    source_id
from {{ ref('int_court_activity') }}

{{ config(
    materialized='incremental',
    unique_key='reservation_id',
    incremental_strategy='merge'
) }}

select
    reservation_id,
    court_number,
    member_id,
    reservation_date,
    reservation_start_at,
    reservation_end_at,
    duration_hours,
    booking_type,
    status,
    booking_source,
    loaded_at
from {{ ref('stg_court_reservations') }}

{% if is_incremental() %}
where loaded_at > (select max(loaded_at) from {{ this }})
{% endif %}

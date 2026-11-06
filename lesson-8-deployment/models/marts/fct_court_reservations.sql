{{ config(
    materialized='incremental',
    unique_key='reservation_id',
    incremental_strategy='merge'
) }}

-- unique_key only decides update-vs-insert against rows already in this
-- table on a *later* run — it does not collapse two genuinely-duplicate
-- source rows landing in the *same* batch (stg_court_reservations has a
-- handful of these by design). Dedupe explicitly instead, keeping each
-- reservation_id's most-recently-loaded copy, so merge always sees a
-- source side with no duplicate keys to match against.
with source as (

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
    -- A 3-day lookback, not a strict "> this table's current max": a row
    -- reloaded with a loaded_at at or below that max (a late-arriving or
    -- corrected load) would otherwise be silently skipped forever.
    where loaded_at > dateadd(day, -3, (select max(loaded_at) from {{ this }}))
    {% endif %}

),

deduplicated as (

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
    from source
    qualify row_number() over (
        partition by reservation_id
        order by loaded_at desc
    ) = 1

)

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
from deduplicated

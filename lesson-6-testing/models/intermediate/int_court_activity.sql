-- Three sources describe time on a court; nothing downstream should have
-- to know that. One shared shape here, so a mart asking "how busy was
-- court 3 last month" doesn't union three tables itself.

with reservations as (

    select
        court_number,
        reservation_date as activity_date,
        reservation_start_at as started_at,
        duration_hours,
        'Court Booking' as activity_type,
        reservation_id as source_id
    from {{ ref('stg_court_reservations') }}
    where booking_type = 'Court Booking'

),

lessons as (

    select
        court_number,
        lesson_date as activity_date,
        lesson_date + start_time as started_at,
        {{ duration_to_hours('duration_minutes') }} as duration_hours,
        'Lesson' as activity_type,
        lesson_id as source_id
    from {{ ref('stg_lessons') }}
    where status = 'Completed'

),

matches as (

    select
        court_number,
        match_date as activity_date,
        match_date + start_time as started_at,
        {{ duration_to_hours('duration_minutes') }} as duration_hours,
        'Match' as activity_type,
        match_id as source_id
    from {{ ref('stg_matches') }}

),

unioned as (

    select * from reservations
    union all
    select * from lessons
    union all
    select * from matches

)

select * from unioned

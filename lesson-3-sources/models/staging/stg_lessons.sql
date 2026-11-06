with source as (

    select * from {{ source('raw', 'lessons') }}

),

renamed as (

    select
        lesson_id,
        member_id,
        coach_id,
        court_number,
        lesson_date,
        start_time,
        duration_minutes,
        lesson_type,
        skill_level,
        price,
        status,
        created_at,
        loaded_at
    from source

)

select * from renamed

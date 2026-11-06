with source as (

    select * from {{ source('raw', 'court_reservations') }}

),

renamed as (

    select
        reservation_id,
        court_number,
        nullif(member_id, '') as member_id,
        reservation_date,

        -- start_time/end_time arrive mixed: most rows are a bare "HH:MM"
        -- string, about 15% are a full "YYYY-MM-DD HH:MM:SS" timestamp.
        -- Normalize both to one real timestamp column rather than carry
        -- the format problem downstream.
        case
            when length(start_time) <= 5
                then cast(reservation_date || ' ' || start_time as timestamp)
            else cast(start_time as timestamp)
        end as reservation_start_at,
        case
            when length(end_time) <= 5
                then cast(reservation_date || ' ' || end_time as timestamp)
            else cast(end_time as timestamp)
        end as reservation_end_at,

        duration_hours,
        booking_type,
        status,
        booking_source,
        created_at,
        loaded_at
    from source

)

select * from renamed

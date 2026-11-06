with source as (

    select * from {{ source('raw', 'matches') }}

),

renamed as (

    select
        match_id,
        tournament_id,
        player1_member_id,
        player2_member_id,
        court_number,
        match_date,
        start_time,
        duration_minutes,
        winner_member_id,
        score,
        round_name,
        loaded_at
    from source

)

select * from renamed

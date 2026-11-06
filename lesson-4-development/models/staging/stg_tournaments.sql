with source as (

    select * from {{ source('raw', 'tournaments') }}

),

renamed as (

    select
        tournament_id,
        name as tournament_name,
        start_date,
        end_date,
        category,
        entry_fee,
        max_participants,
        season_year,
        loaded_at
    from source

)

select * from renamed

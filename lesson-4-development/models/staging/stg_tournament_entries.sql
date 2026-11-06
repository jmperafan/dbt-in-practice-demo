with source as (

    select * from {{ source('raw', 'tournament_entries') }}

),

renamed as (

    select
        entry_id,
        tournament_id,
        member_id,
        registration_date,
        seed,
        entry_fee_paid,
        final_placement,
        loaded_at
    from source

)

select * from renamed

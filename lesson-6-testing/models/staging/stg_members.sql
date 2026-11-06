with source as (

    select * from {{ source('raw', 'members') }}

),

renamed as (

    select
        member_id,
        first_name,
        last_name,
        email,
        phone,
        date_of_birth,
        join_date,
        membership_tier,
        city,
        is_active,
        loaded_at
    from source

)

select * from renamed

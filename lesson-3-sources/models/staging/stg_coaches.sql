with source as (

    select * from {{ source('raw', 'coaches') }}

),

renamed as (

    select
        coach_id,
        first_name,
        last_name,
        email,
        phone,
        hire_date,
        specialty,
        certification_level,
        hourly_rate,
        is_active,
        loaded_at
    from source

)

select * from renamed

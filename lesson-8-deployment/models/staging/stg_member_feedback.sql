with source as (

    select * from {{ source('raw', 'member_feedback') }}

),

renamed as (

    select
        feedback_id,
        member_id,
        category,
        comment_text,
        submitted_date,
        loaded_at
    from source

)

select * from renamed

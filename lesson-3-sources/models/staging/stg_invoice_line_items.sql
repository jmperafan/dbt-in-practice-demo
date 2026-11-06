with source as (

    select * from {{ source('raw', 'invoice_line_items') }}

),

renamed as (

    select
        line_item_id,
        invoice_id,
        category,
        description,
        quantity,
        unit_amount,
        line_amount,
        loaded_at
    from source

)

select * from renamed

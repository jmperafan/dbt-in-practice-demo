with source as (

    select * from {{ source('raw', 'invoices') }}

),

renamed as (

    select
        invoice_id,
        member_id,
        invoice_date,
        due_date,
        total_amount,
        status,
        payment_method,
        paid_date,
        loaded_at
    from source

)

select * from renamed

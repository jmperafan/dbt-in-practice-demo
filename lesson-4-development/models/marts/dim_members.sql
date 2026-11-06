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
    is_active
from {{ ref('stg_members') }}

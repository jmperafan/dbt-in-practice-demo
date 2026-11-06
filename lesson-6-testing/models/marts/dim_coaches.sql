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
    is_active
from {{ ref('stg_coaches') }}

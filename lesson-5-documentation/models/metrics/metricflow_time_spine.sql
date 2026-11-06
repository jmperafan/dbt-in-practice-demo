-- dbt's Semantic Layer requires a time spine model, exactly this name by
-- convention. dbt_utils.date_spine is already installed (a dependency of
-- codegen, see package-lock.yml) — no new package needed for this.

{{ config(materialized='table') }}

with days as (

    {{ dbt_utils.date_spine(
        'day',
        "to_date('01/01/2022', 'mm/dd/yyyy')",
        "to_date('01/01/2030', 'mm/dd/yyyy')"
    ) }}

)

select cast(date_day as date) as date_day
from days

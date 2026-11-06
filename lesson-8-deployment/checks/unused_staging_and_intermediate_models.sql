-- Project clean-up (7.5), promised there and enforced here. Marts
-- terminate the DAG by design — a BI tool or an agent is the real
-- consumer, not another dbt model — so "no downstream dbt edge" isn't
-- the orphan signal there. It is for staging and intermediate: nothing
-- outside this project should ever be the only thing referencing one, so
-- a staging or intermediate model with no downstream model at all is
-- either genuinely new (not wired up yet) or genuinely dead.
select m.unique_id
from {{ info_schema('models') }} as m
left join {{ info_schema('edges') }} as e
  on e.parent_unique_id = m.unique_id
where (m.original_file_path like 'models/staging/%' or m.original_file_path like 'models/intermediate/%')
  and e.child_unique_id is null

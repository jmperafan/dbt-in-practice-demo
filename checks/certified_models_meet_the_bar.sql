-- Model certification (7.6) is a convention, meta.certified: true, not a
-- dbt feature — this check is what actually makes the claim true instead
-- of decorative. A model can't carry the tag unless it clears every part
-- of the bar named in docs/07-governance.md: owned, contracted, and (not
-- checked here, dbt's own test runner already enforces this separately)
-- actually tested.
select unique_id
from {{ info_schema('models') }}
where (meta ->> 'certified') = 'true'
  and (
    meta ->> 'owner' is null
    or trim(meta ->> 'owner') = ''
    or contract_enforced = false
  )

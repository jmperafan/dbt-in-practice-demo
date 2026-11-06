select unique_id
from {{ info_schema('models') }}
where access = 'public'
  and description = ''

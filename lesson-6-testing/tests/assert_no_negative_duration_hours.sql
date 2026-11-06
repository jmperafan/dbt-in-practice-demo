-- A business rule too specific for a generic test: no activity on a
-- court should ever have a negative duration, regardless of which of the
-- three source tables it came from.
select court_activity_id, duration_hours
from {{ ref('fct_court_activity') }}
where duration_hours < 0

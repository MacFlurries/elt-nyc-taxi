select trip_id
from {{ ref('fct_trips') }}
where trip_distance < 0
   or (trip_distance = 0 and total_amount <= 0)

select hour_start
from {{ ref('fct_fleet_hourly') }}
where trips_started < 0
   or peak_concurrent_trips < 0

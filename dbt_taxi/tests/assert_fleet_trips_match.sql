select 1
where (select sum(trips_started) from {{ ref('fct_fleet_hourly') }})
   <> (select count(*) from {{ ref('fct_trips') }})

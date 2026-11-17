select 1
where (select sum(trips) from {{ ref('fct_zone_daytype') }})
   <> (select count(*) from {{ ref('fct_trips') }})

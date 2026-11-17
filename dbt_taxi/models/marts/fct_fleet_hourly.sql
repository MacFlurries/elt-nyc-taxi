{{ config(materialized='table') }}

with ev as (
    select date_trunc('minute', pickup_at) as m, 1 as d from {{ ref('fct_trips') }}
    union all
    select date_trunc('minute', dropoff_at) as m, -1 as d from {{ ref('fct_trips') }}
),
per_minute as (
    select m, sum(d) as delta from ev group by m
),
bounds as (
    select min(date_trunc('minute', pickup_at)) as t0,
           max(date_trunc('minute', pickup_at)) as t1
    from {{ ref('fct_trips') }}
),
grid as (
    select unnest(generate_series(t0, t1, interval 1 minute)) as m from bounds
),
conc as (
    select g.m,
           sum(coalesce(p.delta, 0)) over (order by g.m) as active_trips
    from grid g left join per_minute p using (m)
),
conc_hour as (
    select date_trunc('hour', m) as hour_start,
           max(active_trips) as peak_concurrent_trips
    from conc group by 1
),
trips_hour as (
    select date_trunc('hour', pickup_at) as hour_start,
           count(*) as trips_started,
           avg(date_diff('second', pickup_at, dropoff_at)) / 60.0 as avg_duration_min
    from {{ ref('fct_trips') }} group by 1
)
select
    c.hour_start,
    cast(strftime(cast(c.hour_start as date), '%Y%m%d') as integer) as date_id,
    isodow(c.hour_start) in (6, 7) as is_weekend,
    hour(c.hour_start) as hour_of_day,
    coalesce(t.trips_started, 0) as trips_started,
    t.avg_duration_min,
    c.peak_concurrent_trips
from conc_hour c
left join trips_hour t using (hour_start)

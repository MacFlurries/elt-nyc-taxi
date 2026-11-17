with days as (
    select is_weekend, count(*) as days_in_type
    from {{ ref('dim_date') }}
    group by is_weekend
),
trips as (
    select f.pickup_zone_id, d.is_weekend, count(*) as trips
    from {{ ref('fct_trips') }} f
    join {{ ref('dim_date') }} d on f.pickup_date_id = d.date_id
    group by f.pickup_zone_id, d.is_weekend
)
select
    t.pickup_zone_id,
    z.zone_name,
    z.borough,
    t.is_weekend,
    t.trips,
    x.days_in_type,
    1.0 * t.trips / x.days_in_type as avg_trips_per_day
from trips t
join days x on t.is_weekend = x.is_weekend
left join {{ ref('dim_zone') }} z on t.pickup_zone_id = z.zone_id

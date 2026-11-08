{% if target.type == 'bigquery' %}
with bounds as (
    select
        min(date(pickup_at)) as d0,
        max(date(pickup_at)) as d1
    from {{ ref('stg_yellow_trips') }}
),
days as (
    select date_day
    from bounds, unnest(generate_date_array(d0, d1)) as date_day
)
select
    cast(format_date('%Y%m%d', date_day) as int64)          as date_id,
    date_day,
    extract(year from date_day)                             as year,
    extract(month from date_day)                            as month,
    format_date('%B', date_day)                             as month_name,
    extract(day from date_day)                              as day_of_month,
    mod(extract(dayofweek from date_day) + 5, 7) + 1        as day_of_week,
    format_date('%A', date_day)                             as day_name,
    extract(dayofweek from date_day) in (1, 7)              as is_weekend
from days
{% else %}
with bounds as (
    select
        min(cast(pickup_at as date)) as d0,
        max(cast(pickup_at as date)) as d1
    from {{ ref('stg_yellow_trips') }}
),
days as (
    select cast(unnest(generate_series(d0, d1, interval 1 day)) as date) as date_day
    from bounds
)
select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_id,
    date_day,
    year(date_day)                 as year,
    month(date_day)                as month,
    monthname(date_day)            as month_name,
    day(date_day)                  as day_of_month,
    isodow(date_day)               as day_of_week,
    dayname(date_day)              as day_name,
    isodow(date_day) in (6, 7)     as is_weekend
from days
{% endif %}
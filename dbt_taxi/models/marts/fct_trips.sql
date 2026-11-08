select
    trip_id,
{% if target.type == 'bigquery' %}
    cast(format_date('%Y%m%d', date(pickup_at)) as int64) as pickup_date_id,
{% else %}
    cast(strftime(cast(pickup_at as date), '%Y%m%d') as integer) as pickup_date_id,
{% endif %}
    pickup_location_id   as pickup_zone_id,
    dropoff_location_id  as dropoff_zone_id,
    payment_type_id,
    vendor_id,
    ratecode_id,
    pickup_at,
    dropoff_at,
    passenger_count,
    trip_distance,
    fare_amount,
    tip_amount,
    tolls_amount,
    congestion_surcharge,
    airport_fee,
    cbd_congestion_fee,
    total_amount
from {{ ref('stg_yellow_trips') }}
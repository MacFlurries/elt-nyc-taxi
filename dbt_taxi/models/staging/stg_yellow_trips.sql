select
{% if target.type == 'bigquery' %}
    to_hex(md5(concat(
        coalesce(cast(VendorID as string), ''), '|',
        coalesce(cast(tpep_pickup_datetime as string), ''), '|',
        coalesce(cast(tpep_dropoff_datetime as string), ''), '|',
        coalesce(cast(PULocationID as string), ''), '|',
        coalesce(cast(DOLocationID as string), ''), '|',
        coalesce(cast(total_amount as string), '')
    ))) as trip_id,
{% else %}
    md5(concat_ws('|', VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                  PULocationID, DOLocationID, total_amount)) as trip_id,
{% endif %}
    VendorID               as vendor_id,
    tpep_pickup_datetime   as pickup_at,
    tpep_dropoff_datetime  as dropoff_at,
    passenger_count,
    trip_distance,
    RatecodeID             as ratecode_id,
    PULocationID           as pickup_location_id,
    DOLocationID           as dropoff_location_id,
    payment_type           as payment_type_id,
    fare_amount,
    tip_amount,
    tolls_amount,
    total_amount,
    congestion_surcharge,
    Airport_fee            as airport_fee,
    cbd_congestion_fee,
    file_month
from {{ source('clean', 'yellow_trips') }}
select pickup_zone_id, is_weekend
from {{ ref('fct_zone_daytype') }}
group by pickup_zone_id, is_weekend
having count(*) > 1

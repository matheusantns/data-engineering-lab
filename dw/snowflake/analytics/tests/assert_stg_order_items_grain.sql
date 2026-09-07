select
    order_id,
    variant_id
from {{ ref('stg_order_items') }}
group by order_id, variant_id
having count(*) > 1

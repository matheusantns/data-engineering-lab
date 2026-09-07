select order_id, variant_id
from {{ ref('stg_order_items') }}
where qty <= 0
   or unit_price < 0
   or discount < 0
   or discount > 1
   or line_total < 0

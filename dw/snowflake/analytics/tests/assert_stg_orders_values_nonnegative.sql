select order_id
from {{ ref('stg_orders') }}
where subtotal < 0
   or discount_total < 0
   or shipping_total < 0
   or grand_total < 0

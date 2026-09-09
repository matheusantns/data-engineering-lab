select order_id
from {{ ref('fct_orders') }}
where cast(grand_total as decimal(12, 2))
    <> cast(subtotal - discount_total + shipping_total as decimal(12, 2))

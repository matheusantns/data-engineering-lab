select
    items.order_id,
    orders.date_key,
    orders.customer_key,
    items.variant_id as product_key,
    orders.status,
    orders.currency,
    orders.captured_payment_count > 0 as has_captured_payment,
    items.unit_price,
    items.qty,
    items.discount,
    items.line_total
from {{ ref('stg_order_items') }} as items
inner join {{ ref('fct_orders') }} as orders
    on items.order_id = orders.order_id

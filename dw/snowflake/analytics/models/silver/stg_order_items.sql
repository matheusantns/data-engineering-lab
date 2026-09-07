select
    order_id,
    variant_id,
    product_name,
    sku,
    unit_price,
    qty,
    discount,
    line_total
from {{ source('ecommerce', 'order_items') }}

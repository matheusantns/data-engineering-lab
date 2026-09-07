select
    movement_id,
    variant_id,
    quantity_delta,
    reason,
    order_id,
    convert_timezone('UTC', created_at) as created_at_utc
from {{ source('ecommerce', 'inventory_movements') }}

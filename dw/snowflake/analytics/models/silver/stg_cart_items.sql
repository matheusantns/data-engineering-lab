select
    cart_id,
    variant_id,
    qty,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc
from {{ source('ecommerce', 'cart_items') }}

select
    variant_id,
    quantity_on_hand,
    quantity_reserved,
    convert_timezone('UTC', updated_at) as updated_at_utc
from {{ source('ecommerce', 'inventory') }}

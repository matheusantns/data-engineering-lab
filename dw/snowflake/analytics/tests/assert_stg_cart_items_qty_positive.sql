select cart_id, variant_id
from {{ ref('stg_cart_items') }}
where qty <= 0

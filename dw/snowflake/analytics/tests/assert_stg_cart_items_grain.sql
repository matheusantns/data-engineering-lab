select
    cart_id,
    variant_id
from {{ ref('stg_cart_items') }}
group by cart_id, variant_id
having count(*) > 1

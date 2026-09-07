select
    product_id,
    sort_order
from {{ ref('stg_product_images') }}
group by product_id, sort_order
having count(*) > 1

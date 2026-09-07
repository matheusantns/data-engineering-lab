select variant_id
from {{ ref('stg_product_variants') }}
where price < 0

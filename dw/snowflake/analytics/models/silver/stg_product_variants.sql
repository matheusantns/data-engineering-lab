select
    variant_id,
    product_id,
    sku,
    name,
    price,
    currency,
    attributes,
    is_active,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc
from {{ source('ecommerce', 'product_variants') }}

select
    product_id,
    category_id,
    name,
    slug,
    description,
    attributes,
    is_active,
    search,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc,
    convert_timezone('UTC', deleted_at) as deleted_at_utc
from {{ source('ecommerce', 'products') }}

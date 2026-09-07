select
    image_id,
    product_id,
    url,
    alt_text,
    sort_order,
    convert_timezone('UTC', created_at) as created_at_utc
from {{ source('ecommerce', 'product_images') }}

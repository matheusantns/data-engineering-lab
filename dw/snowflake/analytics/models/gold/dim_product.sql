select
    variants.variant_id as product_key,
    variants.product_id,
    variants.sku,
    products.name as product_name,
    variants.name as variant_name,
    products.category_id,
    categories.name as category_name,
    variants.price as list_price,
    variants.currency,
    products.is_active as product_is_active,
    variants.is_active as variant_is_active
from {{ ref('stg_product_variants') }} as variants
left join {{ ref('stg_products') }} as products
    on variants.product_id = products.product_id
left join {{ ref('stg_categories') }} as categories
    on products.category_id = categories.category_id

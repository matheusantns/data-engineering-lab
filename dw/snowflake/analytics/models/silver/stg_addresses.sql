select
    address_id,
    user_id,
    label,
    line1,
    line2,
    city,
    region,
    postal_code,
    country_code,
    is_default_shipping,
    is_default_billing,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc
from {{ source('ecommerce', 'addresses') }}

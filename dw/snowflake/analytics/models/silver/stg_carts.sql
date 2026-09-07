select
    cart_id,
    user_id,
    session_token,
    status,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc
from {{ source('ecommerce', 'carts') }}

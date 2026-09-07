select
    user_id,
    email,
    first_name,
    last_name,
    company_name,
    phone,
    is_active,
    convert_timezone('UTC', created_at) as created_at_utc,
    convert_timezone('UTC', updated_at) as updated_at_utc,
    convert_timezone('UTC', deleted_at) as deleted_at_utc
from {{ source('ecommerce', 'users') }}

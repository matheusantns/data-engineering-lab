select
    payment_id,
    order_id,
    amount,
    currency,
    provider,
    provider_ref,
    status,
    convert_timezone('UTC', created_at) as created_at_utc
from {{ source('ecommerce', 'payments') }}

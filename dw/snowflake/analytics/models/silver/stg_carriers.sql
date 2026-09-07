select
    carrier_id,
    name,
    phone,
    convert_timezone('UTC', created_at) as created_at_utc
from {{ source('ecommerce', 'carriers') }}

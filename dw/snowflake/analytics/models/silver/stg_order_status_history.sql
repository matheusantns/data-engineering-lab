select
    history_id,
    order_id,
    status,
    note,
    convert_timezone('UTC', changed_at) as changed_at_utc
from {{ source('ecommerce', 'order_status_history') }}

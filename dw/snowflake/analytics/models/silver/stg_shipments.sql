select
    shipment_id,
    order_id,
    carrier_id,
    tracking_number,
    convert_timezone('UTC', shipped_at) as shipped_at_utc,
    convert_timezone('UTC', delivered_at) as delivered_at_utc,
    convert_timezone('UTC', created_at) as created_at_utc
from {{ source('ecommerce', 'shipments') }}

select shipment_id
from {{ ref('stg_shipments') }}
where delivered_at_utc is not null
  and shipped_at_utc is not null
  and delivered_at_utc < shipped_at_utc

select variant_id
from {{ ref('stg_inventory') }}
where quantity_on_hand < 0
   or quantity_reserved < 0

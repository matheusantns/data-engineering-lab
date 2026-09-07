select movement_id
from {{ ref('stg_inventory_movements') }}
where quantity_delta = 0

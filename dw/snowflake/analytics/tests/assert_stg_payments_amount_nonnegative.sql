select payment_id
from {{ ref('stg_payments') }}
where amount < 0

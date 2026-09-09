select
    user_id as customer_key,
    is_active,
    created_at_utc,
    deleted_at_utc is not null as is_deleted
from {{ ref('stg_users') }}

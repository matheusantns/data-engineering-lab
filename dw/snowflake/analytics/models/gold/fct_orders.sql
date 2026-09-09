with payments_by_order as (
    select
        order_id,
        sum(case when status = 'captured' then amount else 0 end) as recognized_revenue,
        sum(case when status = 'refunded' then amount else 0 end) as refunded_amount,
        count(*) as payment_count,
        count_if(status = 'captured') as captured_payment_count,
        count_if(status = 'refunded') as refunded_payment_count
    from {{ ref('stg_payments') }}
    group by order_id
)

select
    orders.order_id,
    to_number(to_char(cast(orders.ordered_at_utc as date), 'YYYYMMDD')) as date_key,
    orders.user_id as customer_key,
    orders.order_number,
    orders.status,
    orders.currency,
    orders.subtotal,
    orders.discount_total,
    orders.shipping_total,
    orders.grand_total,
    coalesce(payments.recognized_revenue, 0::number(38, 2)) as recognized_revenue,
    coalesce(payments.refunded_amount, 0::number(38, 2)) as refunded_amount,
    coalesce(payments.payment_count, 0::number(18, 0)) as payment_count,
    coalesce(payments.captured_payment_count, 0::number(18, 0)) as captured_payment_count,
    coalesce(payments.refunded_payment_count, 0::number(18, 0)) as refunded_payment_count
from {{ ref('stg_orders') }} as orders
left join payments_by_order as payments
    on orders.order_id = payments.order_id

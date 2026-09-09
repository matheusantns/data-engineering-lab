with item_totals as (
    select
        order_id,
        sum(cast(line_total as decimal(12, 2))) as line_total_sum,
        count(*) as item_count
    from {{ ref('fct_order_items') }}
    group by order_id
)

select orders.order_id
from {{ ref('fct_orders') }} as orders
inner join item_totals as items
    on orders.order_id = items.order_id
-- Allow one cent per item for line-level monetary rounding.
where abs(
    cast(items.line_total_sum as decimal(12, 2))
    - cast(orders.subtotal - orders.discount_total as decimal(12, 2))
) > cast(0.01 * items.item_count as decimal(12, 2))

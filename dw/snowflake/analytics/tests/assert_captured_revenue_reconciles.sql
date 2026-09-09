with gold_revenue as (
    select
        currency,
        sum(cast(recognized_revenue as decimal(12, 2))) as recognized_revenue
    from {{ ref('fct_orders') }}
    group by currency
),

captured_payments as (
    select
        currency,
        sum(cast(amount as decimal(12, 2))) as captured_revenue
    from {{ ref('stg_payments') }}
    where status = 'captured'
    group by currency
),

currencies as (
    select currency from gold_revenue
    union
    select currency from captured_payments
)

select currencies.currency
from currencies
left join gold_revenue
    on currencies.currency = gold_revenue.currency
left join captured_payments
    on currencies.currency = captured_payments.currency
where cast(
    coalesce(gold_revenue.recognized_revenue, 0)
    - coalesce(captured_payments.captured_revenue, 0)
    as decimal(12, 2)
) <> cast(0 as decimal(12, 2))

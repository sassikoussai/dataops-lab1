-- Stop the chain if more than 20 % of the rows were rejected.
-- A data test passes when it returns no rows.
select
    count(*) filter (where reject_reason is not null) as n_rejected,
    count(*) as n_total
from {{ ref('int_orders_checked') }}
having count(*) filter (where reject_reason is not null) > 0.20 * count(*)

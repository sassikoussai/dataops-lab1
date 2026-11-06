select *
from {{ ref('int_orders_checked') }}
where reject_reason is not null

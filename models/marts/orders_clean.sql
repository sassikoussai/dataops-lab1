select * exclude (reject_reason)
from {{ ref('int_orders_checked') }}
where reject_reason is null

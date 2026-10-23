REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "country",
    "product",
    "quantity",
    "unit_price",
]

MAX_REJECT_RATE = 0.20


class DataQualityError(Exception):
    """Raised when the data is not good enough to continue."""


def check_schema(df):
    """Stop if a required column is missing or if the file is empty."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataQualityError(f"Missing columns: {missing}")
    if len(df) == 0:
        raise DataQualityError("The file contains no rows")


def check_reject_rate(n_total, n_rejected, max_rate=MAX_REJECT_RATE):
    """Stop if too large a share of the rows was rejected."""
    rate = n_rejected / n_total
    if rate > max_rate:
        raise DataQualityError(
            f"Reject rate too high: {rate:.0%} ({n_rejected}/{n_total} rows rejected, limit is {max_rate:.0%})"
        )

import pandas as pd

MAX_UNIT_PRICE = 1000
ALLOWED_COUNTRIES = ["France", "Germany", "Italy", "Morocco", "Tunisia"]


def _flag(df, mask, reason):
    """Mark the rows selected by `mask` as rejected, unless already rejected."""
    df.loc[mask & df["reject_reason"].isna(), "reject_reason"] = reason


def clean_orders(df):
    """Apply the quality rules. Returns two tables: (clean, rejected)."""
    df = df.copy()
    df["reject_reason"] = None

    # Fixable problem: we repair it instead of rejecting the row.
    df["country"] = df["country"].str.strip().str.title()

    # Rule 1 - completeness: an order must have a customer
    _flag(df, df["customer_id"].isna(), "missing_customer_id")

    # Rule 2 - validity: the date must be a real date (YYYY-MM-DD)
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
    _flag(df, df["order_date"].isna(), "invalid_date")

    # Rule 3 - validity: quantity must be positive
    _flag(df, ~(df["quantity"] > 0), "invalid_quantity")

    # Rule 4 - validity: unit_price must be present, positive and <= MAX_UNIT_PRICE
    _flag(df, ~df["unit_price"].between(0.01, MAX_UNIT_PRICE), "invalid_unit_price")

    # Rule 5 - uniqueness: one row per order_id, keep the first
    _flag(df, df.duplicated("order_id", keep="first"), "duplicate_order_id")
    # Rule 6 - validity: country must be in the list of allowed countries
    _flag(df, ~df["country"].isin(ALLOWED_COUNTRIES), "unknown_country")

    rejected = df[df["reject_reason"].notna()]
    clean = df[df["reject_reason"].isna()].drop(columns="reject_reason")
    return clean, rejected


def revenue_by_country(clean):
    """Transform: total revenue per country."""
    out = clean.assign(revenue=clean["quantity"] * clean["unit_price"])
    out = out.groupby("country", as_index=False)["revenue"].sum()
    out["revenue"] = out["revenue"].round(2)
    return out

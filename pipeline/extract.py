import pandas as pd


def read_orders(path):
    """Extract: read the raw file exactly as it is."""
    return pd.read_csv(path)

import sys

import pandas as pd

path = sys.argv[1]

df = pd.read_csv(path)
df["revenue"] = df["quantity"] * df["unit_price"]

print("Revenue per country")
print(df.groupby("country")["revenue"].sum().round(2))
print()
print("TOTAL:", round(df["revenue"].sum(), 2))

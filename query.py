import sys
import os

import duckdb

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

WAREHOUSE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warehouse.duckdb")
con = duckdb.connect(WAREHOUSE, read_only=True)
result = con.sql(sys.argv[1])
print(result.df().to_string(index=False))

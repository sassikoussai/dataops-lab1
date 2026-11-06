import sys
import os

import duckdb

WAREHOUSE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warehouse.duckdb")


def main(path):
    """Extract + Load: copy the raw file into the warehouse, exactly as it is."""
    # Normalize to forward slashes for DuckDB
    path_fwd = path.replace("\\", "/")
    con = duckdb.connect(WAREHOUSE)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw.orders AS
        SELECT
            *,
            row_number() OVER () AS _row_number,
            '{path_fwd}' AS _source_file,
            current_timestamp AS _loaded_at
        FROM read_csv('{path_fwd}', all_varchar = true, delim = ',', header = true, strict_mode = false)
        """
    )
    n = con.execute("SELECT count(*) FROM raw.orders").fetchone()[0]
    print(f"Loaded {n} rows from {path} into raw.orders")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1])

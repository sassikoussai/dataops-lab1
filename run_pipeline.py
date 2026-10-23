import sys

from pipeline.extract import read_orders
from pipeline.load import write_csv
from pipeline.transform import clean_orders, revenue_by_country
from pipeline.validate import DataQualityError, check_reject_rate, check_schema

OUTPUT_PATH = "data/output/revenue_by_country.csv"
REJECTED_PATH = "data/rejected/rejected_orders.csv"


def main(path):
    print(f"[1/5] Extract        {path}")
    raw = read_orders(path)
    print(f"      {len(raw)} rows read")

    print("[2/5] Check schema")
    check_schema(raw)

    print("[3/5] Clean")
    clean, rejected = clean_orders(raw)
    print(f"      {len(clean)} clean rows, {len(rejected)} rejected rows")
    if len(rejected) > 0:
        print(rejected["reject_reason"].value_counts().to_string())
        write_csv(rejected, REJECTED_PATH)

    print("[4/5] Check quality")
    check_reject_rate(len(raw), len(rejected))

    print("[5/5] Transform and load")
    report = revenue_by_country(clean)
    write_csv(report, OUTPUT_PATH)
    print(report.to_string(index=False))
    print(f"TOTAL: {report['revenue'].sum():.2f}")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except DataQualityError as error:
        print(f"\nPIPELINE STOPPED: {error}")
        print("Nothing was published.")
        sys.exit(1)

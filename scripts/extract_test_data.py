#!/usr/bin/env python3
"""
Extract a subset of meter data from the full Kalmar Energi dataset.

Creates test datasets with configurable number of customers and time range.
Output matches the schema: DateTime,CUSTOMER,AREA,Power_Consumption
"""

import argparse
import csv
import random
import sys
from datetime import datetime
from pathlib import Path

# Source data location (relative to this script)
DEFAULT_SOURCE = Path(__file__).parent.parent.parent / "meterstream-filer/data/final_df.csv/final_df.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Column indices in source file (0-indexed, source has leading index column)
COL_DATETIME = 1
COL_CUSTOMER = 2
COL_AREA = 3
COL_POWER = 5


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract test data subset from full meter dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 50 customers, full 4 years (2020-2023)
  %(prog)s -n 50 -o test_data_large.csv

  # 100 customers, year 2022 only
  %(prog)s -n 100 --start 2022-01-01 --end 2022-12-31 -o test_data_2022.csv

  # 30 customers, 2 years for year-over-year comparison
  %(prog)s -n 30 --start 2022-01-01 --end 2023-12-31 -o test_data_yoy.csv
        """,
    )
    parser.add_argument(
        "-n", "--customers",
        type=int,
        required=True,
        help="Number of customers to include",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2020-01-01",
        help="Start date (YYYY-MM-DD), default: 2020-01-01",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2023-12-31",
        help="End date (YYYY-MM-DD), default: 2023-12-31",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Output filename (will be created in data/ directory)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source CSV file, default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory, default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible customer selection",
    )
    return parser.parse_args()


def collect_customers(source_path: Path) -> set[str]:
    """First pass: collect all unique customer IDs."""
    print(f"Scanning {source_path} for unique customers...")
    customers = set()
    with open(source_path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for i, row in enumerate(reader):
            customers.add(row[COL_CUSTOMER])
            if (i + 1) % 10_000_000 == 0:
                print(f"  Scanned {i + 1:,} rows, found {len(customers):,} unique customers...")
    print(f"  Found {len(customers):,} unique customers")
    return customers


def extract_data(
    source_path: Path,
    output_path: Path,
    selected_customers: set[str],
    start_date: datetime,
    end_date: datetime,
) -> tuple[int, int]:
    """Second pass: extract rows for selected customers within date range."""
    print(f"Extracting data for {len(selected_customers)} customers...")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")

    rows_read = 0
    rows_written = 0

    with open(source_path, "r", newline="") as src, \
         open(output_path, "w", newline="") as dst:

        reader = csv.reader(src)
        writer = csv.writer(dst)

        # Skip source header, write target header
        next(reader)
        writer.writerow(["DateTime", "CUSTOMER", "AREA", "Power_Consumption"])

        for row in reader:
            rows_read += 1

            if row[COL_CUSTOMER] not in selected_customers:
                continue

            # Parse and filter by date
            row_datetime = datetime.strptime(row[COL_DATETIME], "%Y-%m-%d %H:%M:%S")
            if not (start_date <= row_datetime <= end_date):
                continue

            # Write selected columns
            writer.writerow([
                row[COL_DATETIME],
                row[COL_CUSTOMER],
                row[COL_AREA],
                row[COL_POWER],
            ])
            rows_written += 1

            if rows_read % 10_000_000 == 0:
                print(f"  Processed {rows_read:,} rows, written {rows_written:,}...")

    return rows_read, rows_written


def main():
    args = parse_args()

    # Validate source exists
    if not args.source.exists():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    # Parse dates
    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}", file=sys.stderr)
        sys.exit(1)

    if start_date > end_date:
        print("Error: Start date must be before end date", file=sys.stderr)
        sys.exit(1)

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    # First pass: collect all customers
    all_customers = collect_customers(args.source)

    if args.customers > len(all_customers):
        print(f"Warning: Requested {args.customers} customers but only {len(all_customers)} available")
        args.customers = len(all_customers)

    # Select random customers
    selected_customers = set(random.sample(sorted(all_customers), args.customers))
    print(f"Selected {len(selected_customers)} random customers")

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / args.output

    # Second pass: extract data
    rows_read, rows_written = extract_data(
        args.source,
        output_path,
        selected_customers,
        start_date,
        end_date,
    )

    # Report results
    file_size = output_path.stat().st_size
    size_mb = file_size / (1024 * 1024)

    print(f"\nDone!")
    print(f"  Output: {output_path}")
    print(f"  Rows: {rows_written:,}")
    print(f"  Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()

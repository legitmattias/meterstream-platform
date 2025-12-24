#!/usr/bin/env python3
"""
Extract a subset of meter data from the full Kalmar Energi dataset.

Creates test datasets with configurable number of customers and time range.
Output matches the schema: DateTime,CUSTOMER,AREA,Power_Consumption

By default, uses customer IDs that match seeded test users in the auth service.
This ensures portal users can see their own data.
"""

import argparse
import csv
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

# Source data location (relative to this script)
DEFAULT_SOURCE = Path(__file__).parent.parent.parent / "meterstream-filer/data/final_df.csv/final_df.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Customer IDs that match seeded users in auth service (seed_test_data.py)
# These MUST stay in sync with the seeded customer users
SEEDED_CUSTOMER_IDS = {
    "1060598736",  # Alice, Bob, Carl Andersson
    "1060598755",  # Diana, Erik, Fiona Berg
    "1060598764",  # Gustav, Hanna, Ivan Ek
    "1060598773",  # Julia, Karl Lund
    "1060598781",  # Lisa, Martin Holm
    "1060598788",  # Nina Svensson
    "1060598846",  # Oscar Johansson
    "1060598856",  # Petra Karlsson
    "1060598905",  # Quinn Nilsson
    "1060598922",  # Rosa Eriksson
    "1060598963",  # Simon Larsson
    "1060598971",  # Tina Olsson
    "1060598978",  # Ulf Persson
    "1060599019",  # Vera Gustafsson
    "1060599041",  # William Pettersson
    "1060599047",  # Xena Lindberg
    "1060599053",  # Yngve Lindgren
    "1060599059",  # Zara Axelsson
    "1060599082",  # Adam Lindqvist
    "1060599089",  # Bella Magnusson
}

# Column indices in source file (0-indexed, source has leading index column)
COL_DATETIME = 1
COL_CUSTOMER = 2
COL_AREA = 3
COL_POWER = 5


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def count_lines(file_path: Path) -> int:
    """Count lines in file using wc -l for speed."""
    result = subprocess.run(
        ["wc", "-l", str(file_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout.split()[0])


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract test data subset from full meter dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seeded customers (default), 7 days - small dataset
  %(prog)s --start 2020-01-01 --end 2020-01-07 -o test_data_small.csv

  # Seeded customers, 1 month - medium dataset
  %(prog)s --start 2020-01-01 --end 2020-01-31 -o test_data_medium.csv

  # Seeded customers, full 4 years - large dataset
  %(prog)s -o test_data_large.csv

  # Random 50 customers instead of seeded (for testing)
  %(prog)s --random-customers -n 50 -o test_data_random.csv
        """,
    )
    parser.add_argument(
        "-n", "--customers",
        type=int,
        default=None,
        help="Number of customers (only used with --random-customers)",
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
        help="Random seed for reproducible customer selection (only with --random-customers)",
    )
    parser.add_argument(
        "--random-customers",
        action="store_true",
        help="Use random customers instead of seeded customer IDs (requires -n)",
    )
    return parser.parse_args()


def collect_customers(source_path: Path, total_lines: int) -> set[str]:
    """First pass: collect all unique customer IDs."""
    customers = set()
    with open(source_path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in tqdm(reader, total=total_lines - 1, desc="Scanning customers", unit="rows"):
            customers.add(row[COL_CUSTOMER])
    print(f"Found {len(customers):,} unique customers")
    return customers


def extract_data(
    source_path: Path,
    output_path: Path,
    selected_customers: set[str],
    start_date: datetime,
    end_date: datetime,
    total_lines: int,
) -> tuple[int, int]:
    """Second pass: extract rows for selected customers within date range."""
    print(f"Extracting data for {len(selected_customers)} customers...")
    print(f"Date range: {start_date.date()} to {end_date.date()}")

    rows_written = 0

    with open(source_path, "r", newline="") as src, \
         open(output_path, "w", newline="") as dst:

        reader = csv.reader(src)
        writer = csv.writer(dst)

        # Skip source header, write target header
        next(reader)
        writer.writerow(["DateTime", "CUSTOMER", "AREA", "Power_Consumption"])

        for row in tqdm(reader, total=total_lines - 1, desc="Extracting", unit="rows"):
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

    return total_lines - 1, rows_written


def main():
    args = parse_args()

    # Validate arguments
    if args.random_customers and args.customers is None:
        print("Error: --random-customers requires -n/--customers", file=sys.stderr)
        sys.exit(1)

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

    # Count total lines for progress bar
    print("Counting source file lines...")
    total_lines = count_lines(args.source)
    print(f"Source file: {total_lines:,} lines")

    # Select customers: seeded (default) or random
    if args.random_customers:
        # Set random seed if provided
        if args.seed is not None:
            random.seed(args.seed)
            print(f"Using random seed: {args.seed}")

        # First pass: collect all customers from source
        all_customers = collect_customers(args.source, total_lines)

        if args.customers > len(all_customers):
            print(f"Warning: Requested {args.customers} customers but only {len(all_customers)} available")
            args.customers = len(all_customers)

        # Select random customers
        selected_customers = set(random.sample(sorted(all_customers), args.customers))
        print(f"Selected {len(selected_customers)} random customers")
    else:
        # Use seeded customer IDs (matches auth service seed_test_data.py)
        selected_customers = SEEDED_CUSTOMER_IDS.copy()
        print(f"Using {len(selected_customers)} seeded customer IDs (matching auth service)")

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
        total_lines,
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

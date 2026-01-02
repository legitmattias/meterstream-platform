# Test Data

Simulated meter readings based on historical Kalmar Energi data.

## Files

All datasets use the **same 20 seeded customer IDs** that match the test users in `services/auth/src/seed_test_data.py`. This ensures portal users (Alice, Bob, etc.) can see their own data.

| File | Customers | Timespan | Rows | Size |
|------|-----------|----------|------|------|
| `test_data_small.csv` | 20 | 7 days (Jan 1-7, 2020) | ~3,300 | ~160 KB |
| `test_data_medium.csv` | 20 | 3 months (Jan-Mar 2020) | ~43,000 | ~2.1 MB |
| `test_data_large.csv` | 20 | 4 years (2020-2023) | ~280K | ~14 MB |

The large dataset enables year-over-year comparisons in Grafana dashboards.

## Generation

Regenerate datasets using Make targets:
```bash
make extract-small   # 7 days
make extract-medium  # 1 month
make extract-large   # 4 years (full dataset)
```

Or directly with the script:
```bash
python scripts/extract_test_data.py -o test_data_large.csv
```

The script uses seeded customer IDs by default. Use `--random-customers -n 50` for random selection instead.

## CSV Format

```csv
DateTime,CUSTOMER,AREA,Power_Consumption
2020-01-01 00:00:00,1060598736,Kvarnholmen,0.0112
```

| Column | Description |
|--------|-------------|
| DateTime | Timestamp (hourly intervals) |
| CUSTOMER | Customer ID |
| AREA | Geographic area |
| Power_Consumption | kWh consumed |

## Usage

Use with `scripts/produce_test_data.py` to send to the Ingestion Service.

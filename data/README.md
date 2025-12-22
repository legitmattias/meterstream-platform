# Test Data

Simulated meter readings based on historical Kalmar Energi data.

## Files

| File | Customers | Timespan | Rows | Size |
|------|-----------|----------|------|------|
| `test_data_small.csv` | 23 | 7 days (Jan 1-7, 2020) | ~3,860 | ~193 KB |
| `test_data_medium.csv` | 29 | 31 days (Jan 2020) | ~21,240 | ~1.1 MB |
| `test_data_large.csv` | 50 | 4 years (2020-2023) | ~698K | ~34 MB |

The large dataset enables year-over-year comparisons in Grafana dashboards.

**Generation:** `test_data_large.csv` was generated with:
```bash
python scripts/extract_test_data.py -n 50 --seed 42 -o test_data_large.csv
```
The seed ensures reproducible customer selection. The script can generate much larger datasets (e.g., 100+ customers) which should be gitignored due to size.

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

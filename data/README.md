# Test Data

Simulated meter readings based on historical Kalmar Energi data.

## Files

| File | Customers | Timespan | Rows |
|------|-----------|----------|------|
| `test_data_small.csv` | 23 | 7 days (Jan 1-7) | ~3,860 |
| `test_data_medium.csv` | 29 | 31 days (Jan 1-31) | ~21,240 |

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

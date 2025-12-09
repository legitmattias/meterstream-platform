# Scripts

Utility scripts for testing and monitoring.

## Setup

```bash
pip install -r requirements.txt
```

## produce_test_data.py

Sends test data to the Ingestion Service.

```bash
# Send all data from small dataset
python produce_test_data.py

# Send 100 readings slowly (for debugging)
python produce_test_data.py --limit 100 --rate 2

# Use medium dataset with large batches
python produce_test_data.py --file ../data/test_data_medium.csv --batch-size 200
```

**Options:**
- `--file` - CSV file path (default: small dataset)
- `--url` - Ingestion service URL (default: http://localhost:8000)
- `--batch-size` - Readings per request (default: 50)
- `--rate` - Batches per second (default: 10, 0 = unlimited)
- `--limit` - Max readings to send (default: 0 = all)

## nats_status.py

Shows NATS JetStream status (requires port-forward to NATS monitor port).

```bash
kubectl port-forward svc/nats 8222:8222 &
python nats_status.py
```

Output:
```
=== NATS JetStream Status ===
Messages:  1,234
Storage:   45 KB
Streams:   1
Consumers: 1
```

## peek_kalmar1_kafka.js

Peek at Kalmar Energi Team 1's Kafka data stream. Useful for checking their data format.

**Requires Node.js:**
```bash
npm install kafkajs
```

```bash
node peek_kalmar1_kafka.js       # Read 5 messages
node peek_kalmar1_kafka.js 1     # Quick peek at 1 message
node peek_kalmar1_kafka.js 20    # Read 20 messages
```

Note: Their stream uses synthetic meter IDs (`meter-001`, `meter-002`, etc.) that cycle continuously - not suitable for customer-based aggregation.

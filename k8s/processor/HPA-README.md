# HPA (Horizontal Pod Autoscaling) Setup

This document explains how to configure and test automatic scaling for the processor service using KEDA.

## Overview

The processor service automatically scales from 1 to 10 pods based on NATS JetStream queue depth:
- **Min replicas**: 1 (always running)
- **Max replicas**: 10 (under high load)
- **Trigger**: NATS queue depth > 50 messages
- **Polling interval**: 15 seconds
- **Cooldown period**: 60 seconds before scaling down

## Prerequisites

### 1. NATS Consumer Setup

The processor must have a durable consumer configured in NATS JetStream. Check if it exists:

```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer ls METER_DATA
```

If the consumer doesn't exist, create it:

```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer add METER_DATA processor-consumer \
  --pull \
  --deliver all \
  --ack explicit \
  --max-deliver -1 \
  --filter "meter.readings"
```

### 2. Install KEDA

KEDA must be installed in your cluster. You have three options:

#### Option A: Via main playbook (recommended for full deployment)
```bash
ansible-playbook ansible/playbook-k3.yml --tags keda
```

#### Option B: Via dedicated KEDA playbook
```bash
ansible-playbook ansible/playbook-keda.yml
```

#### Option C: Manually with kubectl
```bash
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.16.0/keda-2.16.0.yaml
```

Verify KEDA installation:
```bash
kubectl get pods -n keda
```

Expected output:
```
NAME                                      READY   STATUS    RESTARTS   AGE
keda-operator-xxxxxxxxxx-xxxxx            1/1     Running   0          1m
keda-operator-metrics-apiserver-xxxxx     1/1     Running   0          1m
```

## Deployment

### 1. Apply the ScaledObject manifest

```bash
kubectl apply -f k8s/processor/hpa.yaml
```

### 2. Verify the ScaledObject

```bash
kubectl get scaledobject -n meterstream
```

Expected output:
```
NAME               SCALETARGETKIND      SCALETARGETNAME   MIN   MAX   TRIGGERS     READY
processor-scaler   apps/v1.Deployment   processor         1     10    nats-jetstream   True
```

### 3. Check HPA status

KEDA automatically creates an HPA:
```bash
kubectl get hpa -n meterstream
```

## Testing Scaling Behavior

### Test 1: Generate load to trigger scale-up

You need to send many messages to NATS to trigger scaling. Here's a simple load test script:

```python
# load_test.py
import asyncio
import nats
import json
from datetime import datetime

async def send_messages(count=500):
    nc = await nats.connect("nats://YOUR_CLUSTER_IP:30222")
    js = nc.jetstream()

    print(f"Sending {count} messages...")
    for i in range(count):
        payload = {
            "meter_id": f"meter-{i % 10}",
            "value": 100 + (i % 100),
            "timestamp": datetime.utcnow().isoformat()
        }
        await js.publish("meter.readings", json.dumps(payload).encode())

        if (i + 1) % 100 == 0:
            print(f"Sent {i + 1} messages")

    await nc.close()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(send_messages(500))
```

Replace `YOUR_CLUSTER_IP` with your actual cluster IP.

### Test 2: Monitor scaling in real-time

Open multiple terminal windows:

**Terminal 1: Watch pods**
```bash
watch -n 2 'kubectl get pods -n meterstream | grep processor'
```

**Terminal 2: Watch HPA**
```bash
watch -n 2 'kubectl get hpa -n meterstream'
```

**Terminal 3: Check NATS queue depth**
```bash
watch -n 2 'kubectl exec -it nats-0 -n meterstream -- nats consumer info METER_DATA processor-consumer'
```

**Terminal 4: Run load test**
```bash
python load_test.py
```

### Expected Behavior

1. **Before load**: 1 processor pod running
2. **During load**:
   - NATS queue depth increases (50+ messages)
   - KEDA detects high queue depth
   - New pods start (processor-xxx-2, processor-xxx-3, etc.)
   - Multiple pods consume messages in parallel
3. **After load**:
   - Queue empties
   - After cooldown period (60s), pods scale down to 1

### Test 3: Verify scaling events

Check KEDA logs:
```bash
kubectl logs -n keda deployment/keda-operator -f
```

Check ScaledObject events:
```bash
kubectl describe scaledobject processor-scaler -n meterstream
```

## Troubleshooting

### Scaling not working

1. **Check KEDA is running**
   ```bash
   kubectl get pods -n keda
   ```

2. **Check ScaledObject status**
   ```bash
   kubectl get scaledobject processor-scaler -n meterstream -o yaml
   ```
   Look for `status.conditions` - should show `Ready: True`

3. **Check NATS monitoring endpoint**
   ```bash
   kubectl exec -it nats-0 -n meterstream -- curl localhost:8222/varz
   ```
   Should return JSON with NATS server info

4. **Check consumer exists**
   ```bash
   kubectl exec -it nats-0 -n meterstream -- nats consumer ls METER_DATA
   ```
   Should list `processor-consumer`

### Pods not scaling up

- Verify queue depth exceeds threshold (50 messages)
- Check KEDA operator logs for errors
- Ensure processor deployment has `replicas: 1` (not 0)

### Pods not scaling down

- Wait for cooldown period (60 seconds)
- Check if queue is actually empty
- Verify no new messages arriving

## Metrics and Monitoring

### View current metrics

```bash
kubectl get --raw /apis/external.metrics.k8s.io/v1beta1 | jq .
```

### KEDA metrics server

```bash
kubectl get apiservice v1beta1.external.metrics.k8s.io -o yaml
```

## Configuration Reference

### hpa.yaml parameters

- `minReplicaCount`: Minimum pods (always running)
- `maxReplicaCount`: Maximum pods under load
- `pollingInterval`: How often KEDA checks metrics (seconds)
- `cooldownPeriod`: Wait time before scaling down (seconds)
- `lagThreshold`: Messages in queue to trigger scaling

### Tuning suggestions

For **faster response** to load spikes:
```yaml
pollingInterval: 5   # Check every 5 seconds
lagThreshold: "25"   # Scale at 25 messages
```

For **cost optimization** (slower scaling):
```yaml
pollingInterval: 30  # Check every 30 seconds
cooldownPeriod: 300  # Wait 5 minutes before scale-down
lagThreshold: "100"  # Scale at 100 messages
```

## Demo Procedure for Course

1. **Setup**: Show initial state with 1 pod
   ```bash
   kubectl get pods -n meterstream | grep processor
   ```

2. **Explain**: Show HPA configuration
   ```bash
   kubectl get scaledobject processor-scaler -n meterstream -o yaml
   ```

3. **Load test**: Run message generator
   ```bash
   python load_test.py
   ```

4. **Observe**: Show scaling happening in real-time
   ```bash
   watch kubectl get pods -n meterstream
   ```

5. **Verify**: Show NATS queue being processed
   ```bash
   kubectl exec -it nats-0 -n meterstream -- nats consumer info METER_DATA processor-consumer
   ```

6. **Conclusion**: Show automatic scale-down after load completes

## References

- [KEDA Documentation](https://keda.sh/docs/2.16/)
- [NATS JetStream Scaler](https://keda.sh/docs/2.16/scalers/nats-jetstream/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

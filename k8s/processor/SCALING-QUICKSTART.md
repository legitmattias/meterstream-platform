# HPA Scaling - Quick Start Guide

## What was created

1. **[hpa.yaml](hpa.yaml)** - KEDA ScaledObject manifest for processor autoscaling
2. **[ansible/playbook-keda.yml](../../ansible/playbook-keda.yml)** - Standalone KEDA installation playbook
3. **[ansible/playbook-k3.yml](../../ansible/playbook-k3.yml)** - Main playbook now includes KEDA (with `--tags keda`)
4. **[tests/load_test.py](../../tests/load_test.py)** - Load testing script to trigger scaling
5. **[HPA-README.md](HPA-README.md)** - Full documentation with troubleshooting

## Quick deployment steps

### Step 1: Install KEDA (choose ONE method)

**Method A: Via main playbook with tag**
```bash
ansible-playbook ansible/playbook-k3.yml --tags keda
```

**Method B: Standalone KEDA playbook**
```bash
ansible-playbook ansible/playbook-keda.yml
```

**Method C: Direct kubectl (if you prefer manual)**
```bash
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.16.0/keda-2.16.0.yaml
```

Verify KEDA is running:
```bash
kubectl get pods -n keda
```

### Step 2: Create NATS consumer (if not exists)

Check if consumer exists:
```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer ls METER_DATA
```

If missing, create it:
```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer add METER_DATA processor-consumer \
  --pull \
  --deliver all \
  --ack explicit \
  --max-deliver -1 \
  --filter "meter.readings"
```

### Step 3: Apply HPA manifest

```bash
kubectl apply -f k8s/processor/hpa.yaml
```

Verify:
```bash
kubectl get scaledobject -n meterstream
kubectl get hpa -n meterstream
```

### Step 4: Test scaling

Install dependencies:
```bash
pip install nats-py
```

Port-forward NATS (easier for testing):
```bash
kubectl port-forward -n meterstream svc/nats 4222:4222
```

In another terminal, run load test:
```bash
python tests/load_test.py --count 500
```

Watch pods scale:
```bash
watch kubectl get pods -n meterstream | grep processor
```

## Expected result

```
Before:  processor-xxx-1                    1/1     Running
During:  processor-xxx-1                    1/1     Running
         processor-xxx-2                    1/1     Running  <- NEW!
         processor-xxx-3                    1/1     Running  <- NEW!
         processor-xxx-4                    1/1     Running  <- NEW!
After:   processor-xxx-1                    1/1     Running
```

## Course requirement fulfilled

✓ "At least one microservice must be configured to scale to more than one replica"
- Processor scales from 1 → N pods (max 10)
- Based on NATS queue depth (event-driven)
- Fully automated via KEDA

## What happens behind the scenes

1. Load test sends 500 messages → NATS queue
2. KEDA polls NATS every 15 seconds
3. Queue depth > 50 messages → KEDA triggers scale-up
4. Kubernetes starts new processor pods (2, 3, 4...)
5. Multiple pods consume messages in parallel
6. Queue empties → After 60s cooldown → Scale down to 1 pod

## Files reference

- **Config**: [k8s/processor/hpa.yaml](hpa.yaml)
- **Deploy**: [ansible/playbook-keda.yml](../../ansible/playbook-keda.yml)
- **Test**: [tests/load_test.py](../../tests/load_test.py)
- **Docs**: [HPA-README.md](HPA-README.md)

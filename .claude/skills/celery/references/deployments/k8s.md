---
name: Celery Kubernetes Deployment
description: Kubernetes patterns for celery beat, workers, HPA scaling, and graceful shutdown
---

# Kubernetes Deployment

## Beat — Single Replica, Recreate Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
spec:
  replicas: 1  # CRITICAL: never more than 1
  strategy:
    type: Recreate  # prevents duplicate beats during rollout
  template:
    spec:
      containers:
      - name: beat
        image: ghcr.io/org/backend:latest
        command: ["celery", "-A", "proj", "beat", "-l", "info"]
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef: { name: celery-secrets, key: broker-url }
        resources:
          requests: { cpu: 100m, memory: 128Mi }
          limits: { memory: 256Mi }
```

## Workers — Scalable Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 3
  template:
    spec:
      terminationGracePeriodSeconds: 300  # allow long tasks to finish
      containers:
      - name: worker
        image: ghcr.io/org/backend:latest
        command: ["celery", "-A", "proj", "worker", "-Q", "default",
                  "-c", "4", "-l", "info"]
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: config.settings_celery_light
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef: { name: celery-secrets, key: broker-url }
        lifecycle:
          preStop:
            exec:
              command: ["celery", "-A", "proj", "control", "shutdown"]
        resources:
          requests: { cpu: 500m, memory: 512Mi }
          limits: { memory: 1Gi }
```

## HPA — Autoscale on Queue Length

Use KEDA for queue-based autoscaling:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaler
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:
  - type: redis
    metadata:
      address: redis:6379
      listName: default  # celery queue name
      listLength: "10"   # scale up when >10 pending tasks
```

Or with standard HPA on CPU:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 70 }
```

## Off-Host Workers (API-Only, No DB)

Workers only need broker access and API URL. No DB secrets, no PVCs:

```yaml
env:
- name: DJANGO_SETTINGS_MODULE
  value: config.settings_celery_light  # no DATABASES
- name: INTERNAL_API_URL
  value: http://backend-service:8000/api/internal
- name: INTERNAL_SERVICE_TOKEN
  valueFrom:
    secretKeyRef: { name: celery-secrets, key: internal-token }
```

## Liveness and Readiness

```yaml
livenessProbe:
  exec:
    command: ["celery", "-A", "proj", "inspect", "ping", "-t", "10"]
  initialDelaySeconds: 30
  periodSeconds: 60
readinessProbe:
  exec:
    command: ["celery", "-A", "proj", "inspect", "active", "-t", "10"]
  initialDelaySeconds: 10
  periodSeconds: 30
```

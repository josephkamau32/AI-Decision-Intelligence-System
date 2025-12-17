# Production Deployment Guide

This guide provides comprehensive instructions for deploying the AI Decision Intelligence Platform in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Requirements](#infrastructure-requirements)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Load Balancing and Ingress](#load-balancing-and-ingress)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Configuration](#security-configuration)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling Configuration](#scaling-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Kubernetes cluster (v1.19+) or Docker Compose for simple deployments
- PostgreSQL database (v12+)
- Redis (v6+)
- S3-compatible object storage (optional, for large datasets)
- SSL/TLS certificates
- Domain name with DNS configuration

## Infrastructure Requirements

### Minimum Requirements
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100Mbps

### Recommended Production Setup
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- GPU: NVIDIA GPU (optional, for deep learning workloads)
- Network: 1Gbps+

## Environment Configuration

### Environment Variables

Create a production `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres-host:5432/db_name

# API Keys
OPENAI_API_KEY=your_production_openai_key

# Application Settings
DEBUG=False
SECRET_KEY=your_strong_secret_key_here
APP_NAME=AI Decision Intelligence Platform
VERSION=1.0.0
API_V1_PREFIX=/api/v1

# File Upload
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=1073741824  # 1GB

# MLflow
MLFLOW_TRACKING_URI=file:/app/mlops/experiments
MLFLOW_EXPERIMENT_NAME=AI Decision Intelligence Production

# Redis and Celery
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# Security
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
CORS_ORIGINS=https://your-domain.com

# Monitoring
PROMETHEUS_METRICS_ENABLED=True
LOG_LEVEL=INFO

# Storage (for large datasets)
S3_ENDPOINT=s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=your-bucket-name
```

### Secrets Management

For production, use a secrets management system:

- **Kubernetes**: Use Secrets and ConfigMaps
- **Docker**: Use Docker Secrets
- **Cloud**: AWS Secrets Manager, Azure Key Vault, or GCP Secret Manager

## Database Setup

### PostgreSQL Configuration

1. Create a production database:
```sql
CREATE DATABASE ai_decision_intelligence;
CREATE USER ai_user WITH ENCRYPTED PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE ai_decision_intelligence TO ai_user;
```

2. Configure PostgreSQL for production:
```postgresql.conf
# Connection settings
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Logging
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'
log_duration = on

# Replication (if using replicas)
wal_level = replica
max_wal_senders = 3
```

### Database Migration

Run database migrations if applicable:
```bash
# If using Alembic or similar
alembic upgrade head
```

## Docker Deployment

### Production Docker Compose

Create a `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.prod
    volumes:
      - uploads:/app/uploads
      - mlflow_data:/app/mlops
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - REACT_APP_API_URL=https://api.your-domain.com
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:13-alpine
    environment:
      POSTGRES_DB: ai_decision_intelligence
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: strong_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_user -d ai_decision_intelligence"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.3.0
    command: mlflow server --backend-store-uri postgresql://ai_user:password@postgres:5432/ai_decision_intelligence --default-artifact-root s3://your-bucket/mlflow --host 0.0.0.0 --port 5000
    environment:
      - AWS_ACCESS_KEY_ID=your_access_key
      - AWS_SECRET_ACCESS_KEY=your_secret_key
    depends_on:
      - postgres
    volumes:
      - mlflow_data:/mlflow
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  uploads:
  mlflow_data:
```

### Production Dockerfile

Create `Dockerfile.prod` for optimized builds:

```dockerfile
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /root/.local /root/.local

# Set path
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Kubernetes Deployment

### Namespace Setup

```bash
kubectl create namespace ai-platform
```

### ConfigMaps and Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-platform-config
  namespace: ai-platform
data:
  APP_NAME: "AI Decision Intelligence Platform"
  VERSION: "1.0.0"
  API_V1_PREFIX: "/api/v1"
  LOG_LEVEL: "INFO"

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-platform-secrets
  namespace: ai-platform
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  SECRET_KEY: <base64-encoded-key>
  DATABASE_URL: <base64-encoded-url>
```

### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: ai-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/ai-platform-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        envFrom:
        - configMapRef:
            name: ai-platform-config
        - secretRef:
            name: ai-platform-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: mlflow-data
          mountPath: /app/mlops
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
      - name: mlflow-data
        persistentVolumeClaim:
          claimName: mlflow-pvc
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: ai-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Load Balancing and Ingress

### NGINX Ingress Controller

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-platform-ingress
  namespace: ai-platform
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - your-domain.com
    - api.your-domain.com
    secretName: ai-platform-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

## Monitoring and Logging

### Prometheus and Grafana Setup

```yaml
# prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ai-platform-monitor
  namespace: ai-platform
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Centralized Logging

Use ELK stack or similar:

```yaml
apiVersion: logging.banzaicloud.io/v1beta1
kind: Flow
metadata:
  name: ai-platform-flow
  namespace: ai-platform
spec:
  selectors:
    app: backend
  localOutputRefs:
    - "elasticsearch"
```

## Security Configuration

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: ai-platform
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Security Headers

Configure NGINX with security headers:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Other configurations...
}
```

## Backup and Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres-host -U ai_user -d ai_decision_intelligence > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://your-backup-bucket/
```

### Automated Backups with CronJob

```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: database-backup
  namespace: ai-platform
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13-alpine
            command:
            - /bin/sh
            - -c
            - pg_dump -h postgres -U ai_user -d ai_decision_intelligence | aws s3 cp - s3://your-backup-bucket/backup-$(date +%Y%m%d_%H%M%S).sql
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: ai-platform-secrets
                  key: DB_PASSWORD
          restartPolicy: OnFailure
```

## Scaling Configuration

### Vertical Scaling

```yaml
# Update deployment resources
kubectl patch deployment backend -n ai-platform --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "4Gi"}]'
```

### Horizontal Scaling

```bash
kubectl scale deployment backend --replicas=5 -n ai-platform
```

### Cluster Autoscaling

Configure cluster autoscaler for automatic node scaling based on resource demands.

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   - Check logs: `kubectl logs -f pod-name -n ai-platform`
   - Verify environment variables and secrets
   - Check resource limits

2. **Database Connection Issues**
   - Verify database credentials
   - Check network policies
   - Ensure database is running and accessible

3. **High Memory Usage**
   - Monitor with Prometheus/Grafana
   - Adjust resource limits
   - Optimize application code

4. **Slow API Responses**
   - Check database query performance
   - Verify Redis caching
   - Scale backend pods

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n ai-platform

# View logs
kubectl logs -f deployment/backend -n ai-platform

# Execute commands in pod
kubectl exec -it pod-name -n ai-platform -- /bin/bash

# Check resource usage
kubectl top pods -n ai-platform

# Describe pod for detailed info
kubectl describe pod pod-name -n ai-platform
```

### Health Checks

- **Application Health**: `/api/v1/health`
- **Database Health**: Custom endpoint checking DB connection
- **External Dependencies**: Health checks for Redis, MLflow, etc.

---

For development setup, refer to the main [README.md](README.md). For architecture details, see [architecture.md](architecture.md).
# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured
- Container registry access (GitHub Container Registry)
- Domain name (for ingress)

## Quick Deploy

```bash
# 1. Create namespace
kubectl create namespace ai-platform

# 2. Create secrets (IMPORTANT: Replace placeholder values!)
kubectl create secret generic ai-secrets \
  --from-literal=database_url='postgresql://user:password@postgres:5432/aidb' \
  --from-literal=secret_key='YOUR_RANDOM_SECRET_KEY_HERE' \
  --from-literal=jwt_secret_key='YOUR_JWT_SECRET_KEY_HERE' \
  --from-literal=openai_api_key='sk-YOUR_OPENAI_API_KEY' \
  -n ai-platform

# 3. Update ingress with your domain
# Edit k8s/ingress.yaml and replace 'yourdomain.com'

# 4. Deploy all components
kubectl apply -f k8s/ -n ai-platform

# 5. Check deployment status
kubectl get all -n ai-platform
```

## Deployment Order

The manifests deploy in this order:

1. **ConfigMap** - Application configuration
2. **Secrets** - Sensitive data (manually created)
3. **PersistentVolumeClaims** - Storage
4. **Redis** - Message broker for Celery
5. **MLflow** - Experiment tracking
6. **Backend** - FastAPI application
7. **Frontend** - React UI
8. **Ingress** - External access
9. **HPA** - Auto-scaling

## Verify Deployment

```bash
# Check pods
kubectl get pods -n ai-platform

# Check services
kubectl get svc -n ai-platform

# View logs
kubectl logs -f deployment/ai-backend -n ai-platform
kubectl logs -f deployment/ai-frontend -n ai-platform

# Check ingress
kubectl get ingress -n ai-platform
```

## Access Applications

Once deployed:

- **Frontend**: https://yourdomain.com
- **Backend API**: https://yourdomain.com/api
- **API Docs**: https://yourdomain.com/docs
- **Prometheus Metrics**: https://yourdomain.com/metrics

## Scaling

### Manual Scaling
```bash
kubectl scale deployment ai-backend --replicas=5 -n ai-platform
```

### Auto-Scaling
HPA is configured to scale between 3-10 replicas based on:
- CPU usage > 70%
- Memory usage > 80%

View HPA status:
```bash
kubectl get hpa -n ai-platform
```

## Monitoring

### Prometheus
```bash
# Forward Prometheus port
kubectl port-forward svc/prometheus 9090:9090 -n ai-platform
# Access at http://localhost:9090
```

### Grafana
```bash
# Forward Grafana port
kubectl port-forward svc/grafana 3000:3000 -n ai-platform
# Access at localhost:3000
# Default credentials: admin/admin
```

Import the dashboard from `grafana/dashboards/ml-operations.json`

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n ai-platform
kubectl logs <pod-name> -n ai-platform
```

### Secrets not found
```bash
# Verify secrets exist
kubectl get secrets -n ai-platform

# Recreate if needed
kubectl delete secret ai-secrets -n ai-platform
# Then run create command again
```

### Ingress not working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress ai-ingress -n ai-platform
```

### SSL/TLS Issues
Ensure cert-manager is installed:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

## Updating Deployment

```bash
# Update image version
kubectl set image deployment/ai-backend \
  backend=ghcr.io/yourusername/ai-backend:v2.0.0 \
  -n ai-platform

# Rollout status
kubectl rollout status deployment/ai-backend -n ai-platform

# Rollback if needed
kubectl rollout undo deployment/ai-backend -n ai-platform
```

## Clean Up

```
bash
# Delete all resources
kubectl delete namespace ai-platform
```

## Production Checklist

- [ ] Replace all placeholder secrets
- [ ] Update domain in ingress.yaml
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup strategy for PVCs
- [ ] Configure resource limits appropriately
- [ ] Enable monitoring (Prometheus + Grafana)
- [ ] Set up alerting rules
- [ ] Configure log aggregation
- [ ] Test disaster recovery
- [ ] Document runbook procedures

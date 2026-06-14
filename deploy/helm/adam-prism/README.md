# [PHASE3] Install Adam Prism on Kubernetes with Helm

## Quick Start
```bash
# 1. Generate strong secrets
export ADAM_API_KEY=$(openssl rand -hex 32)
export ADAM_ADMIN_KEY=$(openssl rand -hex 32)
export ADAM_JWT_SECRET=$(openssl rand -hex 32)
export NEXTAUTH_SECRET=$(openssl rand -hex 32)
export GRAFANA_PASSWORD=$(openssl rand -hex 16)

# 2. Install with custom secrets
helm install adam-prism ./adam-prism \
  --set secrets.apiKey=$ADAM_API_KEY \
  --set secrets.adminKey=$ADAM_ADMIN_KEY \
  --set secrets.jwtSecret=$ADAM_JWT_SECRET \
  --set secrets.nextauthSecret=$NEXTAUTH_SECRET \
  --set secrets.grafanaPassword=$GRAFANA_PASSWORD

# 3. Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=adam-prism --timeout=300s

# 4. Check health
kubectl port-forward svc/adam-prism 8000:8000
curl http://localhost:8000/healthz/ready
```

## With PostgreSQL + Redis
```bash
helm install adam-prism ./adam-prism \
  --set database.enabled=true \
  --set redis.enabled=true \
  --set secrets.apiKey=$ADAM_API_KEY \
  ...
```

## With Ingress (production)
```bash
# First install ingress-nginx and cert-manager
helm install adam-prism ./adam-prism \
  --set ingress.hosts[0].host=adam.yourdomain.com \
  --set ingress.tls[0].hosts[0]=adam.yourdomain.com \
  --set ingress.annotations."cert-manager\.io/cluster-issuer"=letsencrypt-prod
```

## Upgrade
```bash
helm upgrade adam-prism ./adam-prism --reuse-values
```

## Uninstall
```bash
helm uninstall adam-prism
# PVCs are NOT deleted by default - run:
kubectl delete pvc -l app.kubernetes.io/instance=adam-prism
```

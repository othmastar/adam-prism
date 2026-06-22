# [PHASE6] GitOps Integration
# ArgoCD + Flux compatible manifests for Adam Prism

## Overview
This directory contains GitOps manifests for deploying Adam Prism using
ArgoCD or Flux CD. The manifests are designed for production-grade
GitOps workflows with:

- Application definitions (Kustomize)
- Image updater configuration
- Notification controllers
- Sync waves for ordered deployments
- RBAC for App-of-Apps pattern

## Quick Start

### ArgoCD
```bash
# Apply the App-of-Apps pattern
kubectl apply -f argo-apps/adam-prism-app.yaml

# Watch sync status
argocd app list -n argocd
argocd app watch adam-prism

# Manual sync
argocd app sync adam-prism
```

### Flux CD
```bash
# Apply the GitRepository + Kustomization
kubectl apply -f flux/adam-prism-source.yaml
kubectl apply -f flux/adam-prism-kustomization.yaml

# Watch
flux get kustomizations --watch
```

## Structure

```
gitops/
├── argocd/
│   ├── app-of-apps.yaml          # ArgoCD Application pointing to this repo
│   ├── adam-prism-app.yaml        # Main Adam Prism application
│   ├── image-updater.yaml        # Automated image updates
│   └── notifications.yaml        # Slack/PagerDuty integration
├── flux/
│   ├── adam-prism-source.yaml    # GitRepository + HelmRepository
│   ├── adam-prism-kustomization.yaml  # Kustomization
│   └── helm-release.yaml         # HelmRelease for Adam Prism
└── README.md
```

## Sync Waves

Resources are deployed in this order (using ArgoCD sync waves):
1. **Wave -5**: Namespaces, secrets (foundation)
2. **Wave -3**: Databases (PostgreSQL, Redis)
3. **Wave -1**: Observability (Prometheus, Grafana)
4. **Wave 0**: Adam Prism API + Web UI
5. **Wave 2**: Channels, integrations
6. **Wave 5**: CronJobs, one-time migrations

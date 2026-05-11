#!/bin/bash

# 1. Create the Kind Cluster
# Uses the auto-detected provider from check_prereqs.sh[cite: 5]
kind create cluster --config kind-cluster.yaml

# 2. Create Namespace
kubectl create namespace argo

# 3. Install Argo Workflows
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/install.yaml

# 4. Patch Argo Server to use NodePort[cite: 6]
# Maps the service to the port defined in kind-cluster.yaml
kubectl patch svc argo-server -n argo -p '{"spec": {"type": "NodePort", "ports": [{"port": 2746, "nodePort": 30000}]}}'

# 5. Configure Auth Mode (Disables login requirements for local dev)[cite: 6]
kubectl patch deployment argo-server -n argo --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--auth-mode=server"}]'

# 6. Step 1.3: Deploy Artifact Storage (MinIO)
kubectl apply -f infrastructure/minio-setup.yaml

# 7. Step 1.4: Apply RBAC Permissions
kubectl apply -f infrastructure/rbac.yaml

# 8. Configure Argo Artifact Repository[cite: 3]
# Create credentials secret for MinIO
kubectl create secret generic argo-artifacts \
  --from-literal=accesskey=admin \
  --from-literal=secretkey=password \
  -n argo

# Patch the controller to use MinIO as the default S3 repository
kubectl patch configmap workflow-controller-configmap -n argo --type merge -p '{"data": {"artifactRepository":"\n  s3:\n    bucket: my-bucket\n    endpoint: minio:9000\n    insecure: true\n    accessKeySecret:\n      name: argo-artifacts\n      key: accesskey\n    secretKeySecret:\n      name: argo-artifacts\n      key: secretkey"}}'

echo "Phase 1 Complete. Argo UI: https://localhost:2746"
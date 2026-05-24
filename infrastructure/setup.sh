#!/bin/bash

ENGINE="docker"
if [ "$KIND_EXPERIMENTAL_PROVIDER" = "podman" ]; then
    ENGINE="podman"
fi

echo "Using container engine: $ENGINE"

# 1. Create Cluster
kind create cluster --config kind-cluster.yaml

# 2. Create Namespace
kubectl create namespace argo

# 3. Deploy Secret FIRST (Fixes MinIO valueFrom dependency)
kubectl create secret generic argo-artifacts \
  --from-literal=accesskey=admin \
  --from-literal=secretkey=password \
  -n argo \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Install Argo Workflows
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/install.yaml

# 5. Patch Service configurations
kubectl patch svc argo-server -n argo -p '{"spec": {"type": "NodePort", "ports": [{"port": 2746, "nodePort": 30000}]}}'
kubectl patch deployment argo-server -n argo --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--auth-mode=server"}]'

# 6. Deploy MinIO (Now safe with emptyDir volume and existing secrets)
kubectl apply -f infrastructure/minio-setup.yaml
kubectl rollout status deployment/minio -n argo --timeout=180s

# 7. Apply Executor permissions
kubectl apply -f infrastructure/rbac.yaml

# 8. Create MinIO Bucket
kubectl run minio-client-create-bucket -n argo --rm -i \
  --image=minio/mc:latest \
  --restart=Never \
  --command -- /bin/sh -c \
  "mc alias set local http://minio:9000 admin password && mc mb --ignore-existing local/my-bucket && mc ls local"

# 9. Configure repository mappings
kubectl patch configmap workflow-controller-configmap -n argo --type merge -p '{"data": {"artifactRepository":"s3:\n  bucket: my-bucket\n  endpoint: minio:9000\n  insecure: true\n  accessKeySecret:\n    name: argo-artifacts\n    key: accesskey\n  secretKeySecret:\n    name: argo-artifacts\n    key: secretkey\n"}}'
kubectl rollout restart deployment/workflow-controller -n argo
kubectl rollout status deployment/workflow-controller -n argo --timeout=180s

# 10. Image deployment
$ENGINE build -t argo-ml:local -f docker/Dockerfile .
mkdir -p kind-images
$ENGINE save argo-ml:local -o ./kind-images/argo-ml-local.tar

CLUSTER_NAME=$(grep 'name:' kind-cluster.yaml | head -n 1 | awk '{print $2}' || echo "kind-cluster")
kind load image-archive ./kind-images/argo-ml-local.tar --name "$CLUSTER_NAME"

echo "Setup Complete!"
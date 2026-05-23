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

# 6. Configure Argo Artifact Repository[cite: 3]
# Create credentials secret for MinIO
kubectl create secret generic argo-artifacts \
  --from-literal=accesskey=admin \
  --from-literal=secretkey=password \
  -n argo \
  --dry-run=client -o yaml | kubectl apply -f -

# 7. Step 1.3: Deploy Artifact Storage (MinIO) and wait for finish
kubectl apply -f infrastructure/minio-setup.yaml
kubectl rollout status deployment/minio -n argo --timeout=180s

# 8. Step 1.4: Apply RBAC Permissions
kubectl apply -f infrastructure/rbac.yaml

# 9. Create MinIO bucket
kubectl run minio-client-create-bucket -n argo --rm -i \
  --image=minio/mc:latest \
  --restart=Never \
  --command -- /bin/sh -c \
  "mc alias set local http://minio:9000 admin password && mc mb --ignore-existing local/my-bucket && mc ls local"

# 10. Patch the controller to use MinIO as the default S3 repository
kubectl patch configmap workflow-controller-configmap -n argo --type merge -p '{"data": {"artifactRepository":"s3:\n  bucket: my-bucket\n  endpoint: minio:9000\n  insecure: true\n  accessKeySecret:\n    name: argo-artifacts\n    key: accesskey\n  secretKeySecret:\n    name: argo-artifacts\n    key: secretkey\n"}}'
kubectl rollout restart deployment/workflow-controller -n argo
kubectl rollout status deployment/workflow-controller -n argo --timeout=180s

# 11. Build Docker Image
docker build -t argo-ml:local -f docker/Dockerfile .

# 12. Save Docker Image
mkdir -p kind-images
docker save argo-ml:local -o ./kind-images/argo-ml-local.tar

#13. Load Docker Image into Kind cluster
ls -lh ./kind-images/argo-ml-local.tar

kind load image-archive ./kind-images/argo-ml-local.tar --name kind-cluster


echo "Setup Complete."
echo "Argo UI: "
echo "  https://localhost:2746"
echo "MinIO UI:"
echo "  kubectl port-forward -n argo svc/minio 9001:9001"

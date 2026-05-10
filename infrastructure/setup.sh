#!/bin/bash

# 1. Create the Cluster
kind create cluster --config kind-cluster.yaml

# 2. Create Namespaces
kubectl create namespace argo

# 3. Install Argo Workflows
# Using the standard install manifest for quick setup
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/install.yaml

# 4. Patch Argo Server to use NodePort
# This connects the service to the port we exposed in kind-cluster.yaml
kubectl patch svc argo-server -n argo -p '{"spec": {"type": "NodePort", "ports": [{"port": 2746, "nodePort": 30000}]}}'

# 5. Disable TLS (Optional for local dev to avoid certificate warnings)
kubectl patch deployment argo-server -n argo --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--auth-mode=server"}]'

echo "Argo is starting. Access it at https://localhost:2746"
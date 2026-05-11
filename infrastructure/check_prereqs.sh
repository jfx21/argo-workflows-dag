#!/bin/bash

# Colors for output
GREEN='\033[0-32m'
RED='\033[0-31m'
NC='\033[0m' # No Color

echo "Checking Prerequisites..."

# Function to check and suggest installation
check_tool() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN} $1 is installed.${NC}"
    else
        echo -e "${RED} $1 is NOT installed.${NC}"
        install_tool $1
    fi
}

install_tool() {
    case $1 in
        docker)
            echo "Please install Docker: https://docs.docker.com/get-docker/"
            ;;
        kind)
            echo "Installing Kind..."
            # For macOS/Linux via Go or Binary
            curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-$(uname)-amd64
            chmod +x ./kind
            sudo mv ./kind /usr/local/bin/kind
            ;;
        kubectl)
            echo "Installing kubectl..."
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/$(uname | tr '[:upper:]' '[:lower:]')/amd64/kubectl"
            chmod +x ./kubectl
            sudo mv ./kubectl /usr/local/bin/kubectl
            ;;
        argo)
            echo "Installing Argo CLI..."
            curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/argo-$(uname | tr '[:upper:]' '[:lower:]')-amd64.gz
            gunzip argo-$(uname | tr '[:upper:]' '[:lower:]')-amd64.gz
            chmod +x argo-$(uname | tr '[:upper:]' '[:lower:]')-amd64
            sudo mv ./argo-$(uname | tr '[:upper:]' '[:lower:]')-amd64 /usr/local/bin/argo
            ;;
    esac
}

# 1. Check Docker/Podman engine (Required for Kind)
if docker info &> /dev/null; then
    echo -e "${GREEN} Docker is running.${NC}"
    export KIND_EXPERIMENTAL_PROVIDER="docker"
elif podman info &> /dev/null; then
    echo -e "${GREEN} Podman is running. Setting provider to podman.${NC}"
    export KIND_EXPERIMENTAL_PROVIDER="podman"
    
    # Auto-set Podman socket if not present
    if [[ -z "$DOCKER_HOST" ]]; then
        PODMAN_SOCK="unix://$(podman machine inspect --format '{{.RuntimeConfig.Address.Path}}' 2>/dev/null || echo "/run/user/$(id -u)/podman/podman.sock")"
        export DOCKER_HOST="$PODMAN_SOCK"
    fi
else
    echo -e "${RED} Error: Neither Docker nor Podman is running.${NC}"
    # If being sourced, don't exit the whole terminal
    return 1 2>/dev/null || exit 1
fi

# 2. Check individual tools
check_tool kind
check_tool kubectl
check_tool argo

echo -e "${GREEN}Environment check complete! Proceed to Phase 1.${NC}"
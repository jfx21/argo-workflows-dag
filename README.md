# Argo Workflows: DAG vs. Steps Benchmarking on Kind

This project demonstrates a multi-stage data/ML pipeline orchestrated by **Argo Workflows** within a local **Kind** (Kubernetes in Docker) cluster. The goal is to evaluate the performance and reliability trade-offs between sequential (Steps) and parallel (DAG) execution models.

## Project Objectives
* **Execution Models:** Compare the latency of `steps` vs. `dag` templates.
* **Artifact Management:** Implement S3-compatible data passing using MinIO.
* **Resilience:** Demonstrate `retryStrategy` and fault-tolerance behavior.
* **Local Dev:** Provide a reproducible K8s environment using Kind.

## Project Structure
- `/infrastructure`: K8s setup (Argo, MinIO)
- `/src`: Pipeline logic (Python)
- `/pipelines`: Argo Workflow YAMLs[cite: 3]
- `/docker`: Containerizatio

## Prerequisites
- Docker or podman
- Kind (Kubernetes in Docker)
- kubectl
- Argo CLI (optional but recommended)

# Execution Guide
## Step 0: Prerequisites Check
Before starting Phase 1, run the prerequisite script to ensure your environment has the necessary tools installed. Run the automated script to verify that `kind`, `kubectl`, and `argo` are in your PATH.
**Note:** You must use `source` so the environment variables (like `KIND_EXPERIMENTAL_PROVIDER`) stay active in your terminal.
```bash
chmod +x infrastructure/check_prereqs.sh
./infrastructure/check_prereqs.sh
```
If you want to use podman:
```bash
source infrastructure/check_prereqs.sh
```

## Step 1: Run setup file
Now that your environment is configured, run the setup script to create the Kind cluster, install Argo Workflows, and configure the UI.

```bash
# Ensure the setup script is executable
chmod +x infrastructure/setup.sh

# Run the setup
./infrastructure/setup.sh
```

**Acessing the dashboard**:
Once the script finishes, open your browser to: `https://localhost:2746`
*Note: Since we are using local self-signed certificates, your browser will show a security warning. Click "Advanced" and "Proceed to localhost" to enter the Argo UI*
# Argo Workflows: DAG vs. Steps Benchmarking on Kind

This project demonstrates a multi-stage data/ML pipeline orchestrated by **Argo Workflows** within a local **Kind** (Kubernetes in Docker) cluster. The goal is to evaluate the performance and reliability trade-offs between sequential (Steps) and parallel (DAG) execution models.

## Project Objectives
* **Execution Models:** Compare the latency of `steps` vs. `dag` templates.
* **Artifact Management:** Implement S3-compatible data passing using MinIO.
* **Resilience:** Demonstrate `retryStrategy` and fault-tolerance behavior.
* **Local Dev:** Provide a reproducible K8s environment using Kind.

## Prerequisites
- Docker or podman
- Kind (Kubernetes in Docker)
- kubectl
- Argo CLI (optional but recommended)
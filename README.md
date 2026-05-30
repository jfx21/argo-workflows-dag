# Argo Workflows: DAG vs. Steps Benchmarking on Kind

This project demonstrates a multi-stage data/ML pipeline orchestrated by **Argo Workflows** within a local **Kind** Kubernetes cluster. The goal is to compare sequential **Steps** workflows with parallel **DAG** workflows, demonstrate artifact handling with MinIO and AWS S3, and show retry/fault-tolerance behavior.

Argo Workflows docs: https://argo-workflows.readthedocs.io/en/latest/

## Project Objectives

- **Execution Models:** compare `steps` and `dag` execution models.
- **Artifact Management:** use MinIO as the local Argo artifact repository.
- **AWS S3 Export:** export intermediate and final pipeline files to AWS S3 using `boto3`.
- **Resilience:** demonstrate `retryStrategy` and failure behavior under shared-resource contention.
- **Local Dev:** provide a reproducible Kubernetes environment using Kind.

## Project Structure

```text
/infrastructure   Kubernetes setup files for Argo, MinIO and RBAC
/src              Python pipeline logic
/pipelines        Argo Workflow YAML files
/docker           Docker image configuration
```

## Prerequisites

- Docker or Podman
- Kind
- kubectl
- Argo CLI
- AWS CLI, only for the optional AWS S3 export variant

---

# Execution Guide

## Step 0: Check prerequisites

Run the prerequisite script to verify that the required tools are available.

```bash
chmod +x infrastructure/check_prereqs.sh
./infrastructure/check_prereqs.sh
```

If you use Podman, source the script so environment variables remain active in the current shell:

```bash
source infrastructure/check_prereqs.sh
```

## Step 1: Create the local environment

Run the setup script to create the Kind cluster, install Argo Workflows, configure MinIO and prepare local artifact storage.

```bash
chmod +x infrastructure/setup.sh
./infrastructure/setup.sh
```

Open the Argo UI at:

```text
https://localhost:2746
```

For local development, MinIO can be opened with:

```bash
kubectl port-forward -n argo svc/minio 9001:9001
```

Credentials:

```text
login: admin
password: password
```

---

# Pipeline Overview

The Python pipeline simulates a typical tabular ML workflow:

```text
generate data -> split data -> preprocess partitions -> merge data -> train model -> evaluate model -> collect metrics
```

## Python stages

### `generate_data.py`

Generates a synthetic tabular dataset.

Parameters:

```text
rows      number of generated rows
features  number of generated feature columns
```

Output:

```text
/mnt/work/raw.csv
```

### `split_data.py`

Splits the generated dataset into row-based partitions.

Output example:

```text
/mnt/work/parts/part-0.csv
/mnt/work/parts/part-1.csv
/mnt/work/parts/part-2.csv
```

Each part contains a subset of rows and all feature columns. In the DAG workflow, the generated `parts.json` file is used to dynamically create preprocessing tasks.

### `preprocess.py`

Processes one data partition. For example, for `part-id=0`, it reads:

```text
/mnt/work/parts/part-0.csv
```

and writes:

```text
/mnt/work/processed/processed-0.csv
```

This is the main parallelizable stage of the pipeline.

### `merge_data.py`

Merges all processed partitions into one dataset:

```text
/mnt/work/merged.csv
```

### `train_model.py`

Trains a simple logistic regression model using `merged.csv`.

Output:

```text
/mnt/work/model.pkl
```

### `evaluate_model.py`

Evaluates the trained model and writes metrics such as accuracy.

Output:

```text
/mnt/work/evaluation-metrics.json
```

### `collect_metrics.py`

Collects per-stage metrics into one summary file.

Output:

```text
/mnt/work/benchmark-summary.json
```

---

# Storage Architecture

The project uses three different storage concepts.

## `/mnt/work` shared workspace

`/mnt/work` is a shared Kubernetes volume mounted into every workflow pod. It is created from the workflow `volumeClaimTemplates` section.

This is the main way data is passed between pipeline stages:

```text
generate-data writes /mnt/work/raw.csv
split-data reads /mnt/work/raw.csv and writes /mnt/work/parts/
preprocess reads /mnt/work/parts/ and writes /mnt/work/processed/
merge-data reads /mnt/work/processed/ and writes /mnt/work/merged.csv
```

So the next pipeline step reads data from `/mnt/work`, not directly from MinIO or AWS S3.

## MinIO artifact repository

MinIO is used as the local S3-compatible artifact repository for Argo Workflows. Argo stores declared `outputs.artifacts` there, for example:

```text
merged.csv
model.pkl
evaluation-metrics.json
benchmark-summary.json
```

MinIO is useful for local development because it is reproducible and does not require external cloud credentials.

## AWS S3 export variant

AWS S3 is used as an additional export target. Because AWS Academy/VocLabs credentials are temporary STS credentials requiring `AWS_SESSION_TOKEN`, direct Argo artifact repository integration with S3 was not used. Instead, selected intermediate and final files are exported to S3 using a Python `boto3` step.

The exported S3 structure is organized by workflow name:

```text
s3://argo-workflows-lsc/runs/<workflow-name>/raw/raw.csv
s3://argo-workflows-lsc/runs/<workflow-name>/parts/part-0.csv
s3://argo-workflows-lsc/runs/<workflow-name>/processed/processed-0.csv
s3://argo-workflows-lsc/runs/<workflow-name>/merged/merged.csv
s3://argo-workflows-lsc/runs/<workflow-name>/model/model.pkl
s3://argo-workflows-lsc/runs/<workflow-name>/evaluation/evaluation-metrics.json
s3://argo-workflows-lsc/runs/<workflow-name>/summary/benchmark-summary.json
```

This demonstrates how local MinIO-based development can be extended with production-style object storage.

---

# Step 2: Build and load the Docker image

Build the pipeline image:

```bash
docker build -t argo-ml:local -f docker/Dockerfile .
```

Load it into the Kind cluster:

```bash
mkdir -p kind-images
docker save argo-ml:local -o ./kind-images/argo-ml-local.tar
kind load image-archive ./kind-images/argo-ml-local.tar --name kind-cluster
```

The image should include all required Python dependencies, including `boto3` for AWS S3 export.

Check that `boto3` is available:

```bash
docker run --rm argo-ml:local -c "import boto3; print('boto3 ok')"
```

If your image does not use Python as the entrypoint, use:

```bash
docker run --rm argo-ml:local python -c "import boto3; print('boto3 ok')"
```

---

# Step 3: Run the ML benchmarks

## DAG workflow with AWS S3 export

```bash
argo submit pipelines/workflow-dag-s3-export.yaml -n argo \
  -p rows=30000 \
  -p features=20 \
  -p parts=3 \
  --watch
```

This workflow dynamically creates preprocessing tasks based on the `parts` parameter. The preprocessing partitions run in parallel.

Example result:

```text
DAG + S3 export
rows=30000, features=20, parts=3
Duration: 1 minute 31 seconds
Progress: 16/16
Status: Succeeded
```

## Steps workflow with AWS S3 export

```bash
argo submit pipelines/workflow-steps-s3-export.yaml -n argo \
  -p rows=30000 \
  -p features=20 \
  --watch
```

This workflow processes three partitions sequentially and is used as the baseline.

Example result:

```text
Steps + S3 export
rows=30000, features=20, parts=3
Duration: 3 minutes 47 seconds
Progress: 16/16
Status: Succeeded
```

## Interpretation

The DAG workflow is faster for the ML pipeline because preprocessing partitions are independent and can run concurrently. The Steps workflow is simpler and more deterministic, but it processes each partition sequentially.

---

# Step 4: Configure AWS S3 export

This project uses AWS S3 as an additional export target, not as the direct Argo artifact repository.

## 1. Set AWS credentials from the lab

Copy the temporary credentials from AWS Academy/VocLabs and set them in the terminal:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"
```

Check access:

```bash
aws sts get-caller-identity
aws s3 ls s3://argo-workflows-lsc
```

If the token expires, copy fresh credentials from the lab and recreate the Kubernetes secret below.

## 2. Create the Kubernetes secret for S3 export

```bash
kubectl delete secret aws-s3-credentials -n argo --ignore-not-found

kubectl create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  --from-literal=AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  --from-literal=AWS_DEFAULT_REGION="us-east-1" \
  -n argo
```

The workflows use this secret in the `export-to-s3` template.

## 3. Verify S3 output

After running a workflow with S3 export:

```bash
aws s3 ls s3://argo-workflows-lsc/runs/ --recursive
```

Expected structure:

```text
runs/<workflow-name>/raw/raw.csv
runs/<workflow-name>/parts/part-0.csv
runs/<workflow-name>/processed/processed-0.csv
runs/<workflow-name>/merged/merged.csv
runs/<workflow-name>/model/model.pkl
runs/<workflow-name>/evaluation/evaluation-metrics.json
runs/<workflow-name>/summary/benchmark-summary.json
```

---

# Step 5: Storage-sensitive benchmark

The normal ML pipeline shows where DAG is useful. The storage-sensitive benchmark shows the opposite case: when tasks compete for a shared limited resource, sequential execution can be safer.

This benchmark uses `storage_sensitive_task.py`, which simulates a shared resource with a lock file:

```text
/mnt/work/shared.lock
```

Only one task can hold the lock at a time.

## Steps storage-sensitive workflow

```bash
argo submit pipelines/workflow-steps-storage-sensitive.yaml -n argo --watch
```

Example result for 6 tasks:

```text
Steps storage-sensitive
Duration: 1 minute 20 seconds
Progress: 7/7
Status: Succeeded
```

The Steps workflow succeeds because tasks run sequentially and do not compete for the lock.

## DAG storage-sensitive workflow

```bash
argo submit pipelines/workflow-dag-storage-sensitive.yaml -n argo --watch
```

Example result for 6 tasks:

```text
DAG storage-sensitive
Duration: 1 minute 0 seconds
Progress: 5/15
Status: Failed
```

The DAG workflow starts tasks concurrently. Several tasks fail and retry because they compete for the same shared resource.

## Interpretation

This benchmark demonstrates that DAG is not always better. DAG is preferable when tasks are independent, but Steps can be better when tasks require strict ordering or controlled access to a shared resource.

---

# Benchmark Summary

## ML pipeline with S3 export

| Workflow | Rows | Features | Parts | Status | Duration |
|---|---:|---:|---:|---|---:|
| DAG + S3 export | 30000 | 20 | 3 | Succeeded | 1m31s |
| Steps + S3 export | 30000 | 20 | 3 | Succeeded | 3m47s |

## Storage-sensitive benchmark

| Workflow | Tasks | Behavior | Status | Duration |
|---|---:|---|---|---:|
| Steps | 4 | Sequential access to shared resource | Succeeded | 1m00s |
| DAG | 4 | Parallel access, retries and failures | Failed | 41s |
| DAG | 4 | Parallel access, succeeds after retries | Succeeded | 1m11s |
| Steps | 6 | Sequential access to shared resource | Succeeded | 1m20s |
| DAG | 6 | More contention, repeated retries | Failed | 1m00s |

---

# Key Conclusions

- DAG is better for independent parallel work, such as preprocessing multiple data partitions.
- Steps is better when tasks require strict ordering or controlled access to a shared resource.
- `/mnt/work` is the actual shared workspace used between workflow steps.
- MinIO is used as the local Argo artifact repository.
- AWS S3 export shows how intermediate and final files can be stored in production-style object storage.
- The AWS S3 export approach was used because AWS Academy credentials require `AWS_SESSION_TOKEN`, while the tested Argo artifact repository configuration did not support this token directly.

---

# Cleanup and Cluster Deletion

To remove the entire local environment and free system resources:

```bash
kind delete cluster --name $(grep 'name:' kind-cluster.yaml | awk '{print $2}' || echo "kind")
```

To clean the S3 test output:

```bash
aws s3 rm s3://argo-workflows-lsc/runs/ --recursive
```

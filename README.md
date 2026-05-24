# Argo Workflows: DAG vs. Steps Benchmarking on Kind

This project demonstrates a multi-stage data/ML pipeline orchestrated by **Argo Workflows** within a local **Kind** (Kubernetes in Docker) cluster. The goal is to evaluate the performance and reliability trade-offs between sequential (Steps) and parallel (DAG) execution models.

Argo Workflows docs: https://argo-workflows.readthedocs.io/en/latest/
## Project Objectives
* **Execution Models:** Compare the latency of `steps` vs. `dag` templates.
* **Artifact Management:** Implement S3-compatible data passing using MinIO.
* **Resilience:** Demonstrate `retryStrategy` and fault-tolerance behavior.
* **Local Dev:** Provide a reproducible K8s environment using Kind.

## Project Structure
- `/infrastructure`: K8s setup (Argo, MinIO)
- `/src`: Pipeline logic (Python)
- `/pipelines`: Argo Workflow YAMLs
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

## Step 2

The Python pipeline simulates a typical data/ML workflow:

```text
generate data -> split data -> preprocess partitions -> merge data -> train model -> evaluate model -> collect metrics
```

### `generate_data.py`

Generates a synthetic tabular dataset. The parameters are:

```text
rows      number of generated rows
features  number of generated feature columns
```

### `split_data.py`

Splits the generated dataset into row-based partitions.

Each part contains a subset of rows and all feature columns.

Argo uses this file to dynamically create preprocessing tasks.

### `preprocess.py`

Processes one partition. For example, for `part-id=0`, it reads:

```text
part-0.csv
```

and writes:

```text
processed-0.csv
```

This stage performs simple feature engineering and normalization. It is the main parallelizable part of the pipeline.

### `merge_data.py`

Merges all processed partitions into one file:

```text
merged.csv
```

### `train_model.py`

Trains a simple logistic regression model using `merged.csv`.

Output:

```text
model.pkl
```

### `evaluate_model.py`

Evaluates the trained model and writes metrics such as accuracy.

Output:

```text
evaluation-metrics.json
```

### `collect_metrics.py`

Collects per-stage metrics into one benchmark file.

Output:

```text
benchmark-summary.json
```

The benchmark summary is stored as an Argo artifact and can be inspected in Argo UI or MinIO.

### Steps and DAG workflow
Workflows will be compared with different values of rows and features of generated data, and different number of parts in which data is split.


For now, the **Steps workflow** is static and processes three partitions sequentially:

```text
generate -> split -> preprocess-0 -> preprocess-1 -> preprocess-2 -> merge -> train -> evaluate -> collect metrics
```

This is used as the sequential baseline.

To run it:
```bash
argo submit pipelines/workflow-steps-3.yaml -n argo   -p rows=<number-of-rows>   -p features=<number-of-features>   --watch
```

The **DAG workflow** is dynamic. It uses the `parts` parameter to automatically create the required number of preprocessing tasks.

To run it:
```bash
argo submit pipelines/workflow-dag.yaml -n argo   -p rows=<number-of-rows>   -p features=<number-of-features> -p parts=<number-of-parts>   --watch
```

This allows comparison between sequential execution and parallel execution. The best way to check saved metrics is by MinIO: 
```bash
kubectl port-forward -n argo svc/minio 9001:9001
```
- login: admin
- password: password

## Step 3: Fault-Tolerance & Resilience Testing

This phase evaluates how the pipeline handles unexpected task failures and executes cleanups.

### 1. Execute the Resilient Pipeline
Submit the workflow containing the retry strategies and exit handlers to the cluster.
```bash
argo submit -n argo --watch pipelines/workflow-resilience.yaml
```

## Cleanup and Cluster Deletion

To remove the entire environment and free up system resources (Docker/Podman containers and volumes), use the following command:

```bash
# Deletes the cluster named in your kind-cluster.yaml
kind delete cluster --name $(grep 'name:' kind-cluster.yaml | awk '{print $2}' || echo "kind")
```
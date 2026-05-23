import json
import os
import time

def file_size(path):
    if path and os.path.exists(path):
        return os.path.getsize(path)
    return None

def write_metrics(metrics_dir, stage, data):
    os.makedirs(metrics_dir, exist_ok=True)

    path = os.path.join(metrics_dir, f"{stage}.json")

    payload = {
        "stage": stage,
        **data
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Metrics written to {path}")

def now():
    return time.time()

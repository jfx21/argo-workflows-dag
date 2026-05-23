import argparse
import json
import os
import glob
import time
import re

parser = argparse.ArgumentParser()
parser.add_argument("--metrics-dir", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--workflow-type", required=True)
parser.add_argument("--rows", required=True)
parser.add_argument("--features", required=True)
parser.add_argument("--parts", required=True)
args = parser.parse_args()

start = time.time()

files = sorted(glob.glob(os.path.join(args.metrics_dir, "*.json")))

records = []

for file in files:
    with open(file) as f:
        records.append(json.load(f))


def stage_sort_key(record):
    stage = record.get("stage", "")

    order = {
        "generate-data": 0,
        "split-data": 1,
        "merge-data": 3,
        "train-model": 4,
        "evaluate-model": 5,
    }

    if stage.startswith("preprocess-"):
        match = re.match(r"preprocess-(\d+)", stage)
        part_id = int(match.group(1)) if match else 999999
        return (2, part_id)

    return (order.get(stage, 999), 0)


records = sorted(records, key=stage_sort_key)

summary = {
    "workflow_type": args.workflow_type,
    "rows": int(args.rows),
    "features": int(args.features),
    "parts": int(args.parts),
    "collected_at_epoch": time.time(),
    "collection_duration_seconds": time.time() - start,
    "stages": records
}

os.makedirs(os.path.dirname(args.output), exist_ok=True)

with open(args.output, "w") as f:
    json.dump(summary, f, indent=2)



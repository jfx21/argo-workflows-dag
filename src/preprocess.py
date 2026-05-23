import argparse
import pandas as pd
import os
import time
import random
import sys
from metrics_utils import write_metrics, file_size

parser = argparse.ArgumentParser()
parser.add_argument("--parts-dir", required=True)
parser.add_argument("--part-id", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--sleep", type=int, default=5)
parser.add_argument("--fail-probability", type=float, default=0.0)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

start = time.time()

if random.random() < args.fail_probability:
    write_metrics(args.metrics_dir, f"preprocess-{args.part_id}", {
        "status": "failed",
        "part_id": args.part_id,
        "duration_seconds": time.time() - start,
        "reason": "simulated failure"
    })
    print("Simulated failure")
    sys.exit(1)

time.sleep(args.sleep)

input_path = os.path.join(args.parts_dir, f"part-{args.part_id}.csv")
output_path = os.path.join(args.output_dir, f"processed-{args.part_id}.csv")

df = pd.read_csv(input_path)

feature_columns = [col for col in df.columns if col.startswith("x")]

for col in feature_columns:
    df[f"{col}_norm"] = (df[col] - df[col].mean()) / (df[col].std() + 1e-9)

df["feature_sum"] = df[feature_columns].sum(axis=1)
df["feature_mean"] = df[feature_columns].mean(axis=1)

df.to_csv(output_path, index=False)

duration = time.time() - start
write_metrics(args.metrics_dir, f"preprocess-{args.part_id}", {
    "status": "succeeded",
    "part_id": int(args.part_id),
    "duration_seconds": duration,
    "sleep_seconds": args.sleep,
    "input_file": input_path,
    "output_file": output_path,
    "rows": len(df),
    "features_processed": len(feature_columns),
    "output_size_bytes": file_size(output_path)
})

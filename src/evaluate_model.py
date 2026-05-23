import argparse
import pandas as pd
import pickle
import json
import os
import time
from metrics_utils import write_metrics, file_size

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--model", required=True)
parser.add_argument("--metrics-output", required=True)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(os.path.dirname(args.metrics_output), exist_ok=True)

start = time.time()

df = pd.read_csv(args.input)

with open(args.model, "rb") as f:
    saved = pickle.load(f)

model = saved["model"]
feature_columns = saved["feature_columns"]

X = df[feature_columns]
y = df["label"]

accuracy = model.score(X, y)

metrics = {
    "accuracy": accuracy,
    "rows": len(df),
    "features": len(feature_columns)
}

with open(args.metrics_output, "w") as f:
    json.dump(metrics, f, indent=2)
    
duration = time.time() - start

write_metrics(args.metrics_dir, "evaluate-model", {
    "duration_seconds": duration,
    "input_file": args.input,
    "model_file": args.model,
    "metrics_output": args.metrics_output,
    "metrics_output_size_bytes": file_size(args.metrics_output),
    **metrics
})
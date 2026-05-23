import argparse
import pandas as pd
import pickle
import os
import time
from sklearn.linear_model import LogisticRegression
from metrics_utils import write_metrics, file_size

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--model-output", required=True)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(os.path.dirname(args.model_output), exist_ok=True)

start = time.time()

df = pd.read_csv(args.input)

feature_columns = [col for col in df.columns if col != "label"]

X = df[feature_columns]
y = df["label"]

model = LogisticRegression(max_iter=100)
model.fit(X, y)

with open(args.model_output, "wb") as f:
    pickle.dump({
        "model": model,
        "feature_columns": feature_columns
    }, f)

duration = time.time() - start

write_metrics(args.metrics_dir, "train-model", {
    "duration_seconds": duration,
    "input_file": args.input,
    "rows": len(df),
    "features": len(feature_columns),
    "model_file": args.model_output,
    "model_size_bytes": file_size(args.model_output)
})
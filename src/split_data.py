import argparse
import pandas as pd
import os
import json
from metrics_utils import write_metrics
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--parts", type=int, default=3)
parser.add_argument("--parts-json", required=True)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)
os.makedirs(os.path.dirname(args.parts_json), exist_ok=True)

start = time.time()

df = pd.read_csv(args.input)

part_ids = []
part_rows = {}


for i in range(args.parts):
    part = df.iloc[i::args.parts]
    path = os.path.join(args.output_dir, f"part-{i}.csv")
    part.to_csv(path, index=False)
    part_ids.append(i)
    part_rows[str(i)] = len(part)
    print(f"Saved {path} with {len(part)} rows")

with open(args.parts_json, "w") as f:
    json.dump(part_ids, f)

duration = time.time() - start

write_metrics(args.metrics_dir, "split-data", {
    "duration_seconds": duration,
    "input_file": args.input,
    "parts": args.parts,
    "part_ids": part_ids,
    "part_rows": part_rows
})
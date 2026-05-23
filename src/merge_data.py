import argparse
import pandas as pd
import os
import glob
import time
from metrics_utils import write_metrics, file_size

parser = argparse.ArgumentParser()
parser.add_argument("--input-dir", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(os.path.dirname(args.output), exist_ok=True)

start = time.time()

files = sorted(glob.glob(os.path.join(args.input_dir, "processed-*.csv")))

if not files:
    raise RuntimeError(f"No processed files found in {args.input_dir}")

print("Merging files:")
for file in files:
    print(file)

dfs = [pd.read_csv(path) for path in files]
merged = pd.concat(dfs, ignore_index=True)
merged.to_csv(args.output, index=False)

duration = time.time() - start
write_metrics(args.metrics_dir, "merge-data", {
    "duration_seconds": duration,
    "input_dir": args.input_dir,
    "input_files_count": len(files),
    "rows": len(merged),
    "output_file": args.output,
    "output_size_bytes": file_size(args.output)
})
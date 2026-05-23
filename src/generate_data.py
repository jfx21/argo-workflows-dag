import argparse
import pandas as pd
import numpy as np
import os
import time
from metrics_utils import write_metrics, file_size

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--rows", type=int, default=10000)
parser.add_argument("--features", type=int, default=10)
parser.add_argument("--metrics-dir", default="/mnt/work/metrics")
args = parser.parse_args()

os.makedirs(os.path.dirname(args.output), exist_ok=True)

start = time.time()
data = {}

for i in range(args.features):
    data[f"x{i+1}"] = np.random.rand(args.rows)

data["label"] = np.random.randint(0, 2, size=args.rows)

df = pd.DataFrame(data)
df.to_csv(args.output, index=False)

duration = time.time() - start
write_metrics(args.metrics_dir, "generate-data", {
    "duration_seconds": duration,
    "rows": args.rows,
    "features": args.features,
    "output_file": args.output,
    "output_size_bytes": file_size(args.output)
})

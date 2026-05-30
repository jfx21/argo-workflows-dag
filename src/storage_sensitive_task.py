import argparse
import json
import os
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--lock-file", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--work-seconds", type=int, default=5)
parser.add_argument("--max-wait-seconds", type=int, default=2)
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

start = time.time()
lock_path = Path(args.lock_file)
output_path = Path(args.output_dir) / f"task-{args.task_id}.json"

while lock_path.exists():
    if time.time() - start > args.max_wait_seconds:
        result = {
            "task_id": args.task_id,
            "status": "failed",
            "reason": "shared resource busy",
            "duration_seconds": time.time() - start,
            "work_seconds": args.work_seconds,
            "max_wait_seconds": args.max_wait_seconds
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    time.sleep(0.2)

try:
    lock_path.write_text(args.task_id)

    print(f"Task {args.task_id} acquired shared resource")
    time.sleep(args.work_seconds)

    result = {
        "task_id": args.task_id,
        "status": "succeeded",
        "reason": "shared resource used successfully",
        "duration_seconds": time.time() - start,
        "work_seconds": args.work_seconds,
        "max_wait_seconds": args.max_wait_seconds
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))

finally:
    if lock_path.exists() and lock_path.read_text() == args.task_id:
        lock_path.unlink()

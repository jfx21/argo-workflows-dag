import argparse
import os
import boto3

parser = argparse.ArgumentParser()
parser.add_argument("--path", required=True)
parser.add_argument("--bucket", required=True)
parser.add_argument("--prefix", required=True)
args = parser.parse_args()

s3 = boto3.client("s3")

def upload_file(local_path, key):
    s3.upload_file(local_path, args.bucket, key)
    print(f"Uploaded {local_path} to s3://{args.bucket}/{key}")

if os.path.isdir(args.path):
    for root, _, files in os.walk(args.path):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, args.path)
            key = f"{args.prefix.rstrip('/')}/{relative_path}"
            upload_file(local_path, key)
else:
    filename = os.path.basename(args.path)
    key = f"{args.prefix.rstrip('/')}/{filename}"
    upload_file(args.path, key)
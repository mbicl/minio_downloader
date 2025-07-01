from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from tqdm import tqdm

import os
import io

# Load environment from .env
load_dotenv()

# Config from env
endpoint     = os.getenv("MINIO_ENDPOINT", "localhost:9000")
access_key   = os.getenv("MINIO_ACCESS_KEY", "ROOTUSER")
secret_key   = os.getenv("MINIO_SECRET_KEY", "CHANGEME123")
secure       = os.getenv("MINIO_SECURE", "false").lower() == "true"
bucket       = os.getenv("MINIO_BUCKET", "recordings")
prefix       = os.getenv("DOWNLOAD_PREFIX", "")
download_dir = os.getenv("DOWNLOAD_DIR", "downloads")

# Init MinIO client
client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

# Download each object with tqdm
objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))

if not objects:
    print("No files found.")
    exit(0)

for obj in objects:
    target_path = os.path.join(download_dir, obj.object_name)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Get the object
    try:
        response = client.get_object(bucket, obj.object_name)
        total = obj.size
        with open(target_path, "wb") as out_file, tqdm(
            desc=obj.object_name,
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.stream(1024 * 1024):  # 1MB chunks
                out_file.write(chunk)
                bar.update(len(chunk))
        response.close()
        response.release_conn()
    except S3Error as err:
        print(f"Failed to download {obj.object_name}: {err}")

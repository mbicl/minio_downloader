from minio import Minio
from minio.error import S3Error
import os
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Read config from environment
endpoint     = os.getenv("MINIO_ENDPOINT", "localhost:9000")
access_key   = os.getenv("MINIO_ACCESS_KEY", "ROOTUSER")
secret_key   = os.getenv("MINIO_SECRET_KEY", "CHANGEME123")
secure       = os.getenv("MINIO_SECURE", "false").lower() == "true"
bucket       = os.getenv("MINIO_BUCKET", "recordings")
prefix       = os.getenv("DOWNLOAD_PREFIX", "")
download_dir = os.getenv("DOWNLOAD_DIR", "downloads")

# Create MinIO client
client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

# Download matching files
objects = client.list_objects(bucket, prefix=prefix, recursive=True)

for obj in objects:
    save_path = os.path.join(download_dir, obj.object_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    print(f"Downloading {obj.object_name} → {save_path}")
    client.fget_object(bucket, obj.object_name, save_path)

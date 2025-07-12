#!/usr/bin/env python3
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
from tqdm import tqdm
import telebot

# ─── Load environment ──────────────────────────────────────────────
load_dotenv()

MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT",  "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "ROOTUSER")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "CHANGEME123")
MINIO_SECURE     = os.getenv("MINIO_SECURE",     "false").lower() == "true"

BUCKET       = os.getenv("MINIO_BUCKET",  "recordings")
PREFIX       = os.getenv("DOWNLOAD_PREFIX", "")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR",   "downloads")
MAX_WORKERS  = int(os.getenv("MAX_DOWNLOAD_THREADS", 8))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MBI_CHAT_ID = os.getenv("MBI_CHAT_ID")

# ─── Initialize client ─────────────────────────────────────────────
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# One global tqdm instance + lock for thread-safe updates
progress_lock = Lock()
progress_bar  = None   # will be initialised in main()

telebot_lock = Lock()  # Lock for thread-safe Telegram bot calls
bot = telebot.TeleBot(BOT_TOKEN)

def mbi_send(message: str) -> None:
    with telebot_lock:
        try:
            bot.send_message(chat_id=MBI_CHAT_ID, text=message)
        except Exception as e:
            with progress_lock:
                progress_bar.write(f"Failed to send message to MBI: {e}")

def download_and_delete(obj):
    """
    Download a single object, update the global progress bar,
    then remove the object from MinIO if the download succeeded.
    """
    tmp_path = Path(DOWNLOAD_DIR) / (obj.object_name + ".tmp")
    target_path = Path(DOWNLOAD_DIR) / obj.object_name
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with client.get_object(BUCKET, obj.object_name) as response, open(tmp_path, "wb") as fp:
            for chunk in response.stream(1024 * 1024):
                fp.write(chunk)
                # Thread-safe bar update
                with progress_lock:
                    progress_bar.update(len(chunk))
        
        if target_path.exists():
            target_path.unlink()  # Remove existing file if it exists
        tmp_path.rename(target_path)
        client.remove_object(BUCKET, obj.object_name)
        mbi_send(f"✓ Downloaded and deleted: {obj.object_name}")
        return f"✓ {obj.object_name}"

    except S3Error as e:
        # Log error without breaking tqdm
        with progress_lock:
            progress_bar.write(f"✗ {obj.object_name}: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return None


def main() -> None:
    global progress_bar

    # Fetch list once
    objects = list(client.list_objects(BUCKET, prefix=PREFIX, recursive=True))
    if not objects:
        print("No files to download.")      # Happens before tqdm exists → safe
        return

    ready_objects = []
    total_bytes   = 0
    for obj in objects:
        tags = client.get_object_tags(BUCKET, obj.object_name)
        if tags.get("state") == "ready":
            ready_objects.append(obj)
            total_bytes += obj.size

    if not ready_objects:
        print("No ready files to download.")
        return
    
    progress_bar = tqdm(
        total=total_bytes,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading",
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(download_and_delete, obj) for obj in ready_objects]
        for f in as_completed(futures):
            result = f.result()
            if result:               # Only successful downloads return text
                with progress_lock:
                    progress_bar.write(result)

    progress_bar.close()
    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if progress_bar:
            with progress_lock:
                progress_bar.close()
        print("\nDownload interrupted by user.")

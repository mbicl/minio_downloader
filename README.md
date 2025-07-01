
# MinIO Video Downloader with Progress Bar

This is a simple Python tool to download video files from a [MinIO](https://min.io/) server, using the MinIO Python SDK and showing download progress with `tqdm`.

---

## ✅ Features

- Downloads files from any S3-compatible MinIO bucket
- Supports recursive download from a given `prefix` (like per-camera folders)
- Automatically recreates directory structure
- Shows a nice progress bar for each file using `tqdm`
- Configurable via `.env` file

---

## 📦 Requirements

- Python 3.12+
- `minio`, `tqdm`, `python-dotenv`

Install with:

```bash
pip install minio tqdm python-dotenv
````

---

## ⚙️ Configuration

Create a `.env` file in the same directory. Sample:

```dotenv
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=ROOTUSER
MINIO_SECRET_KEY=CHANGEME123
MINIO_SECURE=false
MINIO_BUCKET=rec_bucket
DOWNLOAD_PREFIX=cam01/
DOWNLOAD_DIR=downloads
```

- `MINIO_ENDPOINT`: Host and port of your MinIO server
- `MINIO_BUCKET`: The bucket to download from
- `DOWNLOAD_PREFIX`: (optional) Only download files under this path
- `DOWNLOAD_DIR`: Where to store the downloaded files locally

---

## 🚀 Usage

```bash
python3 main.py
```

Downloaded files will appear under `DOWNLOAD_DIR`, preserving the same subfolder structure as in MinIO.

---

## 🧪 Example

If your bucket contains:

```txt
recordings/
├── cam01/2025-06-25_07-45-11.mp4
├── cam01/2025-06-25_07-55-11.mp4
├── cam02/...
```

And your `.env` has `DOWNLOAD_PREFIX=cam01/`, the script will download only `cam01` videos into:

```txt
downloads/cam01/...
```

"""
Storage abstraction — local disk now, GCS later.
To switch to GCS: set STORAGE_BACKEND=gcs in .env and fill in GCS_BUCKET_NAME.
"""
import uuid
import aiofiles
from pathlib import Path
from core.config import get_settings

settings = get_settings()

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_file(data: bytes, original_filename: str) -> str:
    """Save file bytes and return the storage path."""
    ext = Path(original_filename).suffix.lower()
    filename = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / filename
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)
    return str(dest)


async def read_file(storage_path: str) -> bytes:
    async with aiofiles.open(storage_path, "rb") as f:
        return await f.read()


async def delete_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists():
        path.unlink()

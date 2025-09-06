import uuid
import hashlib
import zlib
from pathlib import Path
def find_by_key(items, key, value) -> dict[str, str]|None:
    return next((item for item in items if item.get(key) == value), None) 

def get_uuid_file(id) -> str:
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, str(id)))


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def file_crc32(path: Path) -> str:
    """Возвращает CRC32 файла в little-endian в виде заглавных 8-значных HEX"""
    buf_size = 65536
    crc = 0
    with open(path, "rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            crc = zlib.crc32(data, crc)
    crc = crc & 0xFFFFFFFF
    # Переворачиваем байты для little-endian
    le_bytes = crc.to_bytes(4, 'big')[::-1]
    return le_bytes.hex().upper()
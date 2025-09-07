import uuid
import hashlib
import zlib
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor

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


def download_range(url, start, end, part_file):
    headers = {"Range": f"bytes={start}-{end}"}
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(part_file, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

def parallel_download(url: str, output: str, num_threads: int = 8):
    # Узнаём размер файла
    r = requests.head(url)
    file_size = int(r.headers.get("Content-Length", 0))
    if file_size == 0:
        raise Exception("Не удалось узнать размер файла")

    part_size = file_size // num_threads
    parts = []

    def task(i, start, end):
        part_file = f"{output}.part{i}"
        download_range(url, start, end, part_file)
        return part_file

    # Качаем параллельно
    with ThreadPoolExecutor(max_workers=num_threads) as ex:
        futures = []
        for i in range(num_threads):
            start = i * part_size
            end = (i + 1) * part_size - 1 if i < num_threads - 1 else file_size - 1
            futures.append(ex.submit(task, i, start, end))
        for f in futures:
            parts.append(f.result())

    # Склеиваем части
    with open(output, "wb") as final:
        for part in sorted(parts):
            with open(part, "rb") as pf:
                final.write(pf.read())
            Path(part).unlink()

    print(f"✅ Файл сохранён: {output}")
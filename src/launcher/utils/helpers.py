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

def human_readable_size(num_bytes: int, decimal_places: int = 2) -> str:
    """
    Преобразует число байтов в удобный для чтения формат.
    
    :param num_bytes: количество байтов
    :param decimal_places: количество знаков после запятой
    :return: строка вида '10.23 MB'
    """
    calc_bytes = num_bytes
    if calc_bytes < 0:
        raise ValueError("Размер не может быть отрицательным")
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if calc_bytes < 1000:
            return f"{calc_bytes:.{decimal_places}f} {unit}"
        calc_bytes /= 1000
    return f"{calc_bytes:.{decimal_places}f} PB"
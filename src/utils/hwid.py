import uuid
import platform
import hashlib
import psutil

def get_hwid(salt: str = '') -> str:
    identifiers = []

    # MAC-адрес
    mac = uuid.getnode()
    if (mac >> 40) % 2 == 0:  # реальный, а не случайный
        identifiers.append(hex(mac))

    # Информация о платформе
    identifiers.append(platform.system())
    identifiers.append(platform.machine())
    identifiers.append(platform.node())
    identifiers.append(platform.processor())

    # Диски (серийные номера могут быть недоступны, но используем размер и имя)
    for disk in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(disk.mountpoint)
            identifiers.append(f'{disk.device}:{usage.total}')
        except PermissionError:
            continue

    # Объединяем и хэшируем
    joined = '||'.join(identifiers)
    if salt:
        joined = salt + '||' + joined

    return hashlib.sha256(joined.encode()).hexdigest()

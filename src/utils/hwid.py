import hashlib
import platform
import uuid

import subprocess

def get_hwid(salt: str = '') -> str:
    """
    Возвращает кроссплатформенный уникальный идентификатор машины (HWID)
    """
    system_info = platform.uname()
    sys_data = f"{system_info.system}-{system_info.node}-{system_info.release}-{system_info.version}-{system_info.machine}"

    # Попытка получить MAC-адрес
    try:
        mac = uuid.getnode()
        sys_data += f"-{mac}"
    except:
        pass

    # На Windows можно добавить VolSer или DiskSerial
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic csproduct get UUID", shell=True)
            uuid_str = output.decode().split("\n")[1].strip()
            sys_data += f"-{uuid_str}"
        except:
            pass
    else:
        # На Linux/Mac можно использовать disk UUID
        try:
            if platform.system() == "Linux":
                output = subprocess.check_output("blkid -o value -s UUID $(df / | tail -1 | awk '{print $1}')", shell=True)
                uuid_str = output.decode().strip()
                sys_data += f"-{uuid_str}"
            elif platform.system() == "Darwin":
                output = subprocess.check_output("ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID", shell=True)
                uuid_str = output.decode().split('=')[1].strip().strip('"')
                sys_data += f"-{uuid_str}"
        except:
            pass

    # Хешируем все данные, чтобы получить короткий HWID
    hwid = hashlib.sha256(sys_data.encode()).hexdigest()
    return hwid

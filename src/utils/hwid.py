import hashlib
import platform
import subprocess

def get_hwid(salt: str = '') -> str:
    """
    Возвращает кроссплатформенный уникальный идентификатор машины (HWID)
    """


    # На Windows можно добавить VolSer или DiskSerial
    if platform.system() == "Windows":
        import wmi
        try:
            uuid_str = wmi.WMI().Win32_ComputerSystemProduct()[0].UUID
        except:
            pass
    else:
        # На Linux/Mac можно использовать disk UUID
        try:
            if platform.system() == "Linux":
                output = subprocess.check_output("blkid -o value -s UUID $(df / | tail -1 | awk '{print $1}')", shell=True)
                uuid_str = output.decode().strip()
            elif platform.system() == "Darwin":
                output = subprocess.check_output("ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID", shell=True)
                uuid_str = output.decode().split('=')[1].strip().strip('"')
        except:
            pass

    # Хешируем все данные, чтобы получить короткий HWID
    hwid = hashlib.sha256(uuid_str.encode()).hexdigest()
    return hwid
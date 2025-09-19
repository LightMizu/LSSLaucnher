import os
import platform
from utils.api import API
import shutil

from utils.dota_patcher import restore_dota,patch_dota as patch_d, DOTA_MOD_FOLDER
from utils.helpers import get_folder
from pathlib import Path
from utils.helpers import get_uuid_file
import subprocess
from typing import Union
APP_DATA_PATH:str = str(Path(get_folder())/"packs")
GAMEINFO_SPECIFICBRANCH = "https://raw.githubusercontent.com/SteamDatabase/GameTracking-Dota2/refs/heads/master/game/dota/gameinfo_branchspecific.gi"


# Настроим базовый логгер
def get_dota2_install_path():
    '''
    Returns the Dota 2 installation folder path as a string, or None if not found.
    Works on Windows, macOS, and Linux.
    '''
    system = platform.system()

    if system == 'Windows':
        import winreg
        try:
            # Check common Steam install paths via registry
            reg_path = r'Software\Valve\Steam'
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key: #type: ignore
                    steam_path = winreg.QueryValueEx(key, 'SteamPath')[0] #type: ignore
            except FileNotFoundError:
                # Fallback to default Steam path
                steam_path = os.path.expandvars(r'%ProgramFiles(x86)%\Steam')
            
            dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
            if os.path.exists(dota_path):
                return str(Path(dota_path).resolve())
            
            # Check libraryfolders.vdf for custom library paths
            vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
            if os.path.exists(vdf_path):
                with open(vdf_path, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if '"path"' in line:
                        lib_path = line.split('"')[-2].replace('\\\\', '\\')
                        dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                        if os.path.exists(dota_path):
                            return str(Path(dota_path).resolve())
        except Exception:
            pass

    elif system == 'Darwin':  # macOS
        # Common Steam path on macOS
        steam_path = os.path.expanduser('~/Library/Application Support/Steam')
        dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check libraryfolders.vdf for custom library paths
        vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if '"path"' in line:
                    lib_path = line.split('"')[-2]
                    dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                    if os.path.exists(dota_path):
                        return str(Path(dota_path).resolve())

    elif system == 'Linux':
        # Common Steam path on Linux
        steam_path = os.path.expanduser('~/.steam/steam')
        dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check alternative Steam path
        steam_path = os.path.expanduser('~/.local/share/Steam')
        dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check libraryfolders.vdf for custom library paths
        vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if '"path"' in line:
                    lib_path = line.split('"')[-2]
                    dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                    if os.path.exists(dota_path):
                        return str(Path(dota_path).resolve())

    return None

def install_pack(uuid: str, dota_path: Union[str,Path], api: API):
    dota_path = Path(dota_path)
    data_path = Path(APP_DATA_PATH)
    vpk_file = data_path / uuid
    vpk_folder = dota_path / "game" / DOTA_MOD_FOLDER
    vpk_folder.mkdir(parents=True, exist_ok=True)
    patch_d(dota_path=str(dota_path))
    # Копирование VPK файла
    dest_vpk = vpk_folder / "pak01_dir.vpk"
    shutil.copyfile(vpk_file, dest_vpk)

def launch_dota(extra_args=None):
    """
    Кроссплатформенный запуск Dota 2 через Steam.
    
    :param extra_args: список аргументов запуска (например ["-console", "-novid"])
    """
    system = platform.system()

    if system == "Windows":
        import winreg
        reg_path = r'Software\Valve\Steam'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key: #type: ignore
                steam_path = winreg.QueryValueEx(key, 'SteamPath')[0] #type: ignore
        except FileNotFoundError:
            # Fallback to default Steam path
            steam_path = os.path.expandvars(r'%ProgramFiles(x86)%\Steam')
        steam_cmd = f"{steam_path}\\steam.exe"
    elif system == "Darwin":  # macOS
        steam_cmd = "/Applications/Steam.app/Contents/MacOS/steam_osx"
    elif system == "Linux":
        steam_cmd = "steam"
    else:
        return

    if not os.path.exists(steam_cmd) and system != "Linux":
        return

    cmd = [steam_cmd, "-applaunch", "570"]  # 570 — appid Dota 2
    if extra_args:
        cmd.extend(extra_args)

    subprocess.Popen(cmd)

def delete_pack(dota_path: Union[str,Path]):
    restore_dota(str(dota_path))


def patch_dota(dota_path: Union[str,Path]):
    patch_d(str(dota_path))

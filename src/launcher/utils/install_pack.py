import os
import platform
from src.launcher.utils.api import API
import shutil
from pathlib import Path
from launcher.utils.helpers import get_uuid_file
import subprocess

APP_DATA_PATH = os.getenv('FLET_APP_STORAGE_DATA')
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
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                    steam_path = winreg.QueryValueEx(key, 'SteamPath')[0]
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

def install_pack(uuid: str, dota_path: str, api: API):
    dota_path = Path(dota_path)
    data_path = Path(APP_DATA_PATH)
    game_branch_info_folder = dota_path / "game" / "dota"
    vpk_file = data_path / uuid
    vpk_folder = dota_path / "game" / "Dota2SkinChanger"
    vpk_folder.mkdir(parents=True, exist_ok=True)
    _, game_branch_file = api.get_file(1)
    local_branch_file = get_uuid_file(1)
    for dowl,total in api.download_file(game_branch_file['download_url'], local_branch_file, game_branch_file['md5']):
        pass
    game_branch_file_path = data_path / local_branch_file
    # Копирование gameinfo файла
    dest_gameinfo = game_branch_info_folder / "gameinfo_branchspecific.gi"
    shutil.copyfile(game_branch_file_path, dest_gameinfo)
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
        steam_cmd = "C:\\Program Files (x86)\\Steam\\steam.exe"
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

def delete_pack(dota_path: str, api: API):
    dota_path = Path(dota_path)
    game_branch_info_folder = dota_path / "game" / "dota"
    data_path = Path(APP_DATA_PATH)
    uuid_gameinfo = get_uuid_file("original_gameinfo")
    for dowl,total in api.download_file(GAMEINFO_SPECIFICBRANCH, uuid_gameinfo):
        pass
    game_branch_file_path = data_path / uuid_gameinfo
    # Копирование gameinfo файла
    dest_gameinfo = game_branch_info_folder / "gameinfo_branchspecific.gi"
    shutil.copyfile(game_branch_file_path, dest_gameinfo)

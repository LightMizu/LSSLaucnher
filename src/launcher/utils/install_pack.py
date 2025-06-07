import os
import platform

from pathlib import Path

def get_dota2_install_path():
    """
    Returns the Dota 2 installation folder path as a string, or None if not found.
    Works on Windows, macOS, and Linux.
    """
    system = platform.system()

    if system == "Windows":
        import winreg
        try:
            # Check common Steam install paths via registry
            reg_path = r"Software\Valve\Steam"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
            except FileNotFoundError:
                # Fallback to default Steam path
                steam_path = os.path.expandvars(r"%ProgramFiles(x86)%\Steam")
            
            dota_path = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
            if os.path.exists(dota_path):
                return str(Path(dota_path).resolve())
            
            # Check libraryfolders.vdf for custom library paths
            vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.exists(vdf_path):
                with open(vdf_path, "r") as f:
                    lines = f.readlines()
                for line in lines:
                    if '"path"' in line:
                        lib_path = line.split('"')[-2].replace("\\\\", "\\")
                        dota_path = os.path.join(lib_path, "steamapps", "common", "dota 2 beta")
                        if os.path.exists(dota_path):
                            return str(Path(dota_path).resolve())
        except Exception:
            pass

    elif system == "Darwin":  # macOS
        # Common Steam path on macOS
        steam_path = os.path.expanduser("~/Library/Application Support/Steam")
        dota_path = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check libraryfolders.vdf for custom library paths
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                if '"path"' in line:
                    lib_path = line.split('"')[-2]
                    dota_path = os.path.join(lib_path, "steamapps", "common", "dota 2 beta")
                    if os.path.exists(dota_path):
                        return str(Path(dota_path).resolve())

    elif system == "Linux":
        # Common Steam path on Linux
        steam_path = os.path.expanduser("~/.steam/steam")
        dota_path = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check alternative Steam path
        steam_path = os.path.expanduser("~/.local/share/Steam")
        dota_path = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
        if os.path.exists(dota_path):
            return str(Path(dota_path).resolve())

        # Check libraryfolders.vdf for custom library paths
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                if '"path"' in line:
                    lib_path = line.split('"')[-2]
                    dota_path = os.path.join(lib_path, "steamapps", "common", "dota 2 beta")
                    if os.path.exists(dota_path):
                        return str(Path(dota_path).resolve())

    return None
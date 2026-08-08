import os
import platform
from utils.api import API
import shutil
import tempfile
import zipfile
from utils.dota_patcher import restore_dota, patch_dota as patch_d, DOTA_MOD_FOLDER
from utils.helpers import get_folder
from pathlib import Path
import subprocess
from typing import Union
from loguru import logger

APP_DATA_PATH: str = str(Path(get_folder()) / "packs")
GAMEINFO_SPECIFICBRANCH = "https://raw.githubusercontent.com/SteamDatabase/GameTracking-Dota2/refs/heads/master/game/dota/gameinfo_branchspecific.gi"


class CustomPackInstallError(Exception):
    pass


def get_dota2_install_path():
    """
    Returns the Dota 2 installation folder path as a string, or None if not found.
    Works on Windows, macOS, and Linux.
    """
    logger.info("Searching for Dota 2 installation path...")
    system = platform.system()

    if system == 'Windows':
        import winreg
        try:
            reg_path = r'Software\Valve\Steam'
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:  # type: ignore
                    steam_path = winreg.QueryValueEx(key, 'SteamPath')[0]  # type: ignore
            except FileNotFoundError:
                steam_path = os.path.expandvars(r'%ProgramFiles(x86)%\Steam')
            dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
            if os.path.exists(dota_path):
                logger.info(f"Dota 2 found at {dota_path}")
                return str(Path(dota_path).resolve())
            vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
            if os.path.exists(vdf_path):
                with open(vdf_path, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if '"path"' in line:
                        lib_path = line.split('"')[-2].replace('\\\\', '\\')
                        dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                        if os.path.exists(dota_path):
                            logger.info(f"Dota 2 found at {dota_path}")
                            return str(Path(dota_path).resolve())
        except Exception as e:
            logger.error(f"Failed to detect Dota 2 installation path: {e}")

    elif system == 'Darwin':  # macOS
        steam_path = os.path.expanduser('~/Library/Application Support/Steam')
        dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
        if os.path.exists(dota_path):
            logger.info(f"Dota 2 found at {dota_path}")
            return str(Path(dota_path).resolve())
        vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if '"path"' in line:
                    lib_path = line.split('"')[-2]
                    dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                    if os.path.exists(dota_path):
                        logger.info(f"Dota 2 found at {dota_path}")
                        return str(Path(dota_path).resolve())

    elif system == 'Linux':
        steam_paths = [os.path.expanduser('~/.steam/steam'), os.path.expanduser('~/.local/share/Steam')]
        for steam_path in steam_paths:
            dota_path = os.path.join(steam_path, 'steamapps', 'common', 'dota 2 beta')
            if os.path.exists(dota_path):
                logger.info(f"Dota 2 found at {dota_path}")
                return str(Path(dota_path).resolve())
            vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
            if os.path.exists(vdf_path):
                with open(vdf_path, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if '"path"' in line:
                        lib_path = line.split('"')[-2]
                        dota_path = os.path.join(lib_path, 'steamapps', 'common', 'dota 2 beta')
                        if os.path.exists(dota_path):
                            logger.info(f"Dota 2 found at {dota_path}")
                            return str(Path(dota_path).resolve())

    logger.warning("Dota 2 installation path not found")
    return None


def install_pack(uuid: str, dota_path: Union[str, Path], api: API):
    dota_path = Path(dota_path)
    data_path = Path(APP_DATA_PATH)
    vpk_folder = dota_path / "game" / DOTA_MOD_FOLDER
    vpk_folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"Installing pack '{uuid}' to {vpk_folder}")
    patch_d(dota_path=str(dota_path))

    source_path = data_path / uuid
    if source_path.suffix.lower() == ".zip":
        installed_files = _install_zip_pack(source_path, vpk_folder)
    else:
        installed_files = _install_single_vpk(source_path, vpk_folder)

    logger.success(
        f"Pack '{uuid}' installed successfully ({len(installed_files)} vpk files)"
    )


def _clear_installed_vpks(vpk_folder: Path):
    for existing_vpk in vpk_folder.glob("*.vpk"):
        logger.info(f"Removing previously installed pack file '{existing_vpk.name}'")
        existing_vpk.unlink()


def _install_single_vpk(vpk_file: Path, vpk_folder: Path) -> list[Path]:
    if not vpk_file.is_file():
        raise FileNotFoundError(vpk_file)

    _clear_installed_vpks(vpk_folder)
    dest_vpk = vpk_folder / "pak01_dir.vpk"
    shutil.copyfile(vpk_file, dest_vpk)
    return [dest_vpk]


def _install_zip_pack(zip_path: Path, vpk_folder: Path) -> list[Path]:
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)

    logger.info(f"Extracting custom pack archive '{zip_path.name}'")
    with tempfile.TemporaryDirectory(prefix="lsslauncher-pack-") as temp_dir:
        extract_dir = Path(temp_dir)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        vpk_files = sorted(
            path
            for path in extract_dir.rglob("*")
            if path.is_file() and path.suffix.lower() == ".vpk"
        )
        if not vpk_files:
            raise CustomPackInstallError(
                f"No .vpk files found in archive '{zip_path.name}'"
            )

        installed_files: list[Path] = []
        installed_names: set[str] = set()
        for source_vpk in vpk_files:
            if source_vpk.name in installed_names:
                raise CustomPackInstallError(
                    f"Archive '{zip_path.name}' contains duplicate VPK names: '{source_vpk.name}'"
                )
            installed_names.add(source_vpk.name)

        _clear_installed_vpks(vpk_folder)
        for source_vpk in vpk_files:
            dest_vpk = vpk_folder / source_vpk.name
            logger.info(f"Installing VPK '{source_vpk.name}' from archive")
            shutil.move(str(source_vpk), dest_vpk)
            installed_files.append(dest_vpk)

        return installed_files


def launch_dota(extra_args=None):
    """
    Cross-platform launch of Dota 2 via Steam.
    :param extra_args: list of launch arguments (e.g., ["-console", "-novid"])
    """
    system = platform.system()
    logger.info("Launching Dota 2...")

    if system == "Windows":
        import winreg
        reg_path = r'Software\Valve\Steam'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:  # type: ignore
                steam_path = winreg.QueryValueEx(key, 'SteamPath')[0]  # type: ignore
        except FileNotFoundError:
            steam_path = os.path.expandvars(r'%ProgramFiles(x86)%\Steam')
        steam_cmd = f"{steam_path}\\steam.exe"
    elif system == "Darwin":
        steam_cmd = "/Applications/Steam.app/Contents/MacOS/steam_osx"
    elif system == "Linux":
        steam_cmd = "steam"
    else:
        logger.error(f"Unsupported platform: {system}")
        return

    if not os.path.exists(steam_cmd) and system != "Linux":
        logger.error(f"Steam executable not found: {steam_cmd}")
        return

    cmd = [steam_cmd, "-applaunch", "570"]  # 570 — Dota 2 appid
    if extra_args:
        cmd.extend(extra_args)

    subprocess.Popen(cmd)
    logger.success("Dota 2 launched")


def delete_pack(dota_path: Union[str, Path]):
    logger.info("Deleting installed pack and restoring original files...")
    restore_dota(str(dota_path))
    logger.success("Pack deleted and Dota restored")


def patch_dota(dota_path: Union[str, Path]):
    logger.info("Patching Dota 2...")
    patch_d(str(dota_path))
    logger.success("Dota 2 patched successfully")

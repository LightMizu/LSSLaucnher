import shutil
import hashlib
import zlib
from pathlib import Path
import psutil
from loguru import logger

DOTA_MOD_FOLDER = "DotaLSS"

def is_dota2_running():
    logger.info("Checking if Dota 2 is currently running...")
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower().startswith("dota2"):
            logger.warning("Dota 2 is currently running!")
            return True
    logger.info("Dota 2 is not running")
    return False


def calculate_hashes(file_path: Path):
    logger.info(f"Calculating SHA1 and CRC32 for {file_path}")
    sha1 = hashlib.sha1()
    crc32 = 0
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha1.update(chunk)
            crc32 = zlib.crc32(chunk, crc32)
    sha1_hex = sha1.hexdigest().upper()
    crc_hex = format(crc32 & 0xFFFFFFFF, '08X')
    logger.info(f"Calculated hashes - SHA1: {sha1_hex}, CRC32: {crc_hex}")
    return sha1_hex, crc_hex


def validate_patch_state(gameinfo_path: Path, dota_signatures_path: Path):
    logger.info("Validating patch state...")
    gameinfo_patched = False
    dota_signatures_patched = False

    with open(gameinfo_path, 'r', encoding='utf-8', errors='ignore') as f:
        contents = f.read()
        if "// Patched by" in contents:
            gameinfo_patched = True
            logger.info("gameinfo is already patched")

    with open(dota_signatures_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
        if lines:
            last_line = lines[-1]
            if last_line.startswith("..."):
                actual_sha1, actual_crc32 = calculate_hashes(gameinfo_path)
                try:
                    _, info = last_line.split("~", 1)
                    sha1_part, crc_part = info.split(";")
                    sha1 = sha1_part.split(":")[1].strip()
                    crc32 = crc_part.split(":")[1].strip()
                    if actual_sha1 == sha1 and actual_crc32 == crc32:
                        dota_signatures_patched = True
                        logger.info("dota.signatures is already patched")
                except Exception:
                    logger.error("Failed to validate dota.signatures entry")

    return gameinfo_patched, dota_signatures_patched


def backup_file(path: Path, new_ext: str):
    backup = path.with_suffix(new_ext)
    if not backup.exists():
        shutil.copy(path, backup)
        logger.info(f"Backup created: {path} -> {backup}")
    else:
        logger.info(f"Backup already exists: {backup}")


def modify_gameinfo(gameinfo_path: Path):
    logger.info(f"Modifying gameinfo file: {gameinfo_path}")
    with open(gameinfo_path, 'r', encoding='utf-8', errors='ignore') as f:
        contents = f.read()

    insert = '''
        SearchPaths // Patched by LSSLauncher
        {
            Game_Language       dota_*LANGUAGE*

            Game_LowViolence    dota_lv

            Game                %s
            Game                dota
            Game                core

            Mod                 %s
            Mod                 dota

            Write               dota

            AddonRoot_Language  dota_*LANGUAGE*_addons

            AddonRoot           dota_addons

            PublicContent       dota_core
            PublicContent       core
        }
    ''' % (DOTA_MOD_FOLDER, DOTA_MOD_FOLDER)
    idx = contents.find("FileSystem")
    if idx == -1:
        logger.error("FileSystem section not found in gameinfo")
        raise RuntimeError("Unable to find FileSystem section in gameinfo")
    br_idx = contents.find("}", idx)
    if br_idx == -1:
        logger.error("Closing bracket for FileSystem not found")
        raise RuntimeError("Unable to find closing bracket for FileSystem")

    new_content = contents[:br_idx] + insert + contents[br_idx:]
    with open(gameinfo_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    logger.info("gameinfo file successfully modified")


def modify_dota_signatures(dota_signatures_path: Path, sha1: str, crc32: str):
    logger.info(f"Appending new patch entry to {dota_signatures_path}")
    with open(dota_signatures_path, 'a', encoding='utf-8') as f:
        patch = f"...\\..\\..\\dota\\gameinfo_branchspecific.gi~SHA1:{sha1};CRC:{crc32}"
        f.write("\n" + patch)
    logger.info("dota.signatures updated successfully")


def patch_dota(dota_path: str):
    if is_dota2_running():
        return 1

    game_path = Path(dota_path)
    gameinfo_path = game_path / "game/dota/gameinfo_branchspecific.gi"
    dota_signatures_path = game_path / "game/bin/win64/dota.signatures"
    mod_dir_path = game_path / f"game/{DOTA_MOD_FOLDER}"

    gameinfo_patched, dota_signatures_patched = validate_patch_state(gameinfo_path, dota_signatures_path)

    if not gameinfo_patched:
        backup_file(gameinfo_path, ".gi_backup")
        modify_gameinfo(gameinfo_path)
    if not dota_signatures_patched:
        backup_file(dota_signatures_path, ".signatures_backup")
        sha1, crc32 = calculate_hashes(gameinfo_path)
        modify_dota_signatures(dota_signatures_path, sha1, crc32)

    if not mod_dir_path.exists():
        mod_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Mod directory created: {mod_dir_path}")

    logger.success("Patch applied successfully!")


def restore_dota(dota_path: str):
    game_path = Path(dota_path)
    gameinfo_path = game_path / "game/dota/gameinfo_branchspecific.gi"
    dota_signatures_path = game_path / "game/bin/win64/dota.signatures"

    backup_gameinfo = gameinfo_path.with_suffix(".gi_backup")
    backup_signatures = dota_signatures_path.with_suffix(".signatures_backup")

    if backup_gameinfo.exists():
        shutil.copy(backup_gameinfo, gameinfo_path)
        logger.info("Restored gameinfo from backup")
    else:
        logger.warning("No backup found for gameinfo")

    if backup_signatures.exists():
        shutil.copy(backup_signatures, dota_signatures_path)
        logger.info("Restored dota.signatures from backup")
    else:
        logger.warning("No backup found for dota.signatures")

    mod_dir_path = game_path / f"game/{DOTA_MOD_FOLDER}"
    if mod_dir_path.exists():
        shutil.rmtree(mod_dir_path)
        logger.info("Removed mod directory")

    logger.success("Restore completed successfully!")

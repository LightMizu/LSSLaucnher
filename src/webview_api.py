import json
import sys
import threading
import time
import webbrowser
from logging import log
from pathlib import Path
from typing import Any, Dict, List, Optional

import webview
from loguru import logger
from playsound3 import playsound

from utils.api import API
from utils.auth import AuthUtil
from utils.helpers import get_folder, get_uuid_file, human_readable_size
from utils.install_pack import (
    APP_DATA_PATH,
    delete_pack,
    get_dota2_install_path,
    launch_dota,
    patch_dota,
)
from utils.install_pack import (
    install_pack as install_pack_func,
)

PERSISTENCE_FILE = Path(get_folder()) / "persistence.json"
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

if hasattr(sys, "_MEIPASS"):
    sound_path = Path(sys._MEIPASS) / "assets" / "notification.mp3"  # ignore
else:
    sound_path = current_dir.parent / "src" / "assets" / "notification.mp3"


class PyWebAPI:
    def __init__(self):
        self.api = API()
        self.auth = AuthUtil(self.api)
        self.state = self._load_state()
        self._download_cancel: dict[str, threading.Event] = {}
        self._download_lock = threading.Lock()
        # Initialize API token if present
        if self.state.get("token"):
            self.api.token = self.state["token"]

        self.current_mix_result_key = None
        self.mix_running = False

        # Cache for get_files
        self.files_cache = None
        self.files_cache_time = 0
        self.CACHE_DURATION = 300  # 5 minutes

    def _load_state(self) -> Dict[str, Any]:
        if PERSISTENCE_FILE.exists():
            try:
                with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Backward-compatible defaults for newly added settings keys.
                    loaded.setdefault("favorites", [])
                    loaded.setdefault("installed_packs", [])
                    loaded.setdefault("token", None)
                    loaded.setdefault("dota_path", "")
                    loaded.setdefault("sound_enabled", True)
                    loaded.setdefault("settings", {})
                    return loaded
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {
            "favorites": [],
            "installed_packs": [],
            "token": None,
            "dota_path": "",
            "sound_enabled": True,
            "settings": {},
        }

    def _invalidate_cache(self):
        self.files_cache = None
        self.files_cache_time = 0
        logger.debug("Cache invalidated")

    def _save_state(self):
        try:
            with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _get_window(self):
        if webview.windows:
            return webview.windows[0]
        return None

    # =====================
    # GENERAL
    # =====================

    def get_about_data(self):
        # Using the hardcoded data from the example as requested to strictly follow the structure
        return {
            "appName": "LSS Launcher",
            "logoUrl": "https://i.imgur.com/yeCIPkD.png",
            "team": [
                {
                    "name": "BoneByte",
                    "role": "Developer",
                    "avatarUrl": "https://i.imgur.com/HQP9lIr.png",
                },
                {
                    "name": "Lsq",
                    "role": "Designer",
                    "avatarUrl": "https://i.imgur.com/CaeeUha.png",
                },
                {
                    "name": "Darkness",
                    "role": "Mod Creator",
                    "avatarUrl": "https://i.imgur.com/Pk0fgRX.png",
                },
            ],
            "changelog": [
                {
                    "version": "2.0.1",
                    "date": "25-02-2026",
                    "changes": [
                        "Исправленна кнопка скриншотов в главном меню",
                        "Исправленна кнопка переключениязвука в настроках",
                    ],
                },
                {
                    "version": "2.0.0",
                    "date": "25-02-2026",
                    "changes": [
                        "Полный редизайн интерфейса",
                    ],
                },
            ],
            "socials": [
                {"id": "telegram", "title": "Telegram", "icon": "telegram"},
            ],
        }

    def action(self, name: str, payload: dict):
        logger.info(f"ACTION: {name} {payload}")
        if payload["id"] == "telegram":
            webbrowser.open("https://t.me/lssnews")
        return {"ok": True}

    def open_pack_dir(self):
        try:
            import os

            packs_path = Path(APP_DATA_PATH)
            if packs_path.exists():
                os.startfile(str(packs_path))
            else:
                logger.error(f"Pack directory not found: {packs_path}")
        except Exception as e:
            logger.error(f"Failed to open pack directory: {e}")

    def open_log_folder(self):
        try:
            import os

            APP_LOG_PATH = Path(get_folder()) / "logs"
            log_path = Path(APP_LOG_PATH)
            if log_path.exists():
                os.startfile(str(log_path))
            else:
                logger.error(f"Log directory not found: {packs_path}")
        except Exception as e:
            logger.error(f"Failed to open log directory: {e}")

    def delete_cache(self):
        import shutil

        shutil.rmtree(Path(APP_DATA_PATH))

    # =====================
    # SHOP
    # =====================

    def get_shop_items(self):
        current_time = time.time()

        # Check cache
        if self.files_cache and (
            current_time - self.files_cache_time < self.CACHE_DURATION
        ):
            files = self.files_cache
            logger.debug("Using cached files list")
        else:
            status, files = self.api.get_files(0, 100)
            if status != 200:
                return self.files_cache if self.files_cache else []
            self.files_cache = files
            self.files_cache_time = current_time
            logger.debug("Fetched new files list from API")

        # Transform to frontend expected format
        favorites = set(self.state.get("favorites", []))
        installed_ids = set(self.state.get("installed_packs", []))

        # Pre-calculate local file existence for all items to minimize IO in loop if possible,
        # but here we iterate anyway.
        from utils.api import APP_DATA_PATH

        packs_path = Path(APP_DATA_PATH)

        items = []
        for f in files:
            # Map existing fields to frontend fields
            # Frontend expects: id, name, size, category, isFavorite
            # Backend provides: id, name, size, type (maybe?), etc.
            # Assuming 'type' or similar maps to category, or hardcoding 'visual'
            # Looking at home.py, it uses file["id"], file["name"], file["size"]

            id_str = str(f.get("id"))
            is_installed = id_str in installed_ids

            name_file = get_uuid_file(id_str)  # Ensure string
            local_path = packs_path / name_file
            is_downloaded = local_path.exists()

            items.append(
                {
                    "id": id_str,  # Frontend expects string ID? Example uses "visual_pack_1"
                    "name": f.get("name"),
                    "size": human_readable_size(f.get("size", 0)),  # Use helper
                    "category": "visual",  # Defaulting for now as backend data structure isn't fully clear on category
                    "isFavorite": id_str in favorites,
                    "isInstalled": is_installed,
                    "isDownloaded": is_downloaded,
                    # Store original data for download
                    "_original": f,
                }
            )
        return items

    def get_installed_packs(self) -> List[str]:
        return list(self.state.get("installed_packs", []))

    def get_favorites(self) -> List[str]:
        return list(self.state.get("favorites", []))

    # =====================
    # LOGIN MENU
    # =====================

    def is_login(self) -> bool:
        if self.api.token:
            return self.auth.check_token_is_valid()
        return False

    def log(self, *args):
        logger.debug(f"{args}")

    def login(self, username: str, password: str, remember: bool) -> int:
        # We need HWID
        from utils.hwid import get_hwid

        hwid = get_hwid()

        status = self.api.get_token(username, password, hwid)
        if status == 200 and remember:
            self.state["token"] = self.api.token
            self._save_state()
        return status

    # =====================
    # MIX MENU
    # =====================

    def start_mix(self, mainId: str, subId: str):

        def worker():
            try:
                # 1. Resolve IDs to keys
                status, files = self.api.get_files(0, 100)
                main_file = next(
                    (f for f in files if str(f["id"]) == str(mainId)), None
                )
                sub_file = next((f for f in files if str(f["id"]) == str(subId)), None)

                if not main_file or not sub_file:
                    logger.error("Could not find files for mix")
                    return

                # 2. Start merge task
                status, task_id = self.api.merge_pack(
                    main_file["s3_key"], sub_file["s3_key"]
                )
                if status != 200:
                    logger.error(f"Merge failed to start: {status}")
                    return

                # 3. Poll for completion
                self.mix_running = True
                result_key = None
                for _ in range(60 * 20):  # 60 seconds timeout (approx)
                    if not self.mix_running:
                        break
                    time.sleep(1)
                    s_code, task_data = self.api.get_task_status(task_id)
                    if task_data.get("progress") == "Status.DONE":
                        result_key = task_data.get("result_key")
                        break

                if result_key:
                    self.current_mix_result_key = result_key
                    webview.windows[0].evaluate_js(
                        f'window.__lsslauncher_on_mix_ready?.("merge")'
                    )
                else:
                    logger.error("Merge timed out or failed")
                    webview.windows[0].evaluate_js(
                        f'window.__lsslauncher_on_mix_error?.("Черезмерное ожидание")'
                    )
            except Exception as e:
                logger.error(f"Error in start_mix: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def download_mix(self):
        if not self.current_mix_result_key:
            return

        def worker():
            try:
                uuid = Path(self.current_mix_result_key).stem
                url = f"https://{self.current_mix_result_key}"  # Assuming result_key is partial URL based on merge.py
                # merge.py: f"https://{self.result_key}"

                # Verify dota path
                dota_path = self._ensure_dota_path()
                if not dota_path:
                    logger.error("Dota path not found")
                    return

                for progress in self.api.download_file(url, uuid, None):
                    webview.windows[0].evaluate_js(
                        f"window.__lsslauncher_on_mix_progress?.({progress})"
                    )

                install_pack_func(uuid, dota_path, self.api)

                webview.windows[0].evaluate_js("window.__lsslauncher_on_mix_done?.()")
            except Exception as e:
                logger.error(f"Error in download_mix: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def cancel_mix(self):
        self.mix_running = False
        print("Mix canceled")

    # =====================
    # HOME MENU
    # =====================
    def close(self):
        webview.windows[0].destroy()

    def minimize(self):
        webview.windows[0].minimize()

    def launch_game(self):
        launch_dota()

    def update_fix(self):
        dota_path = self._ensure_dota_path()
        if dota_path:
            patch_dota(dota_path)
            webview.windows[0].evaluate_js(
                f"window.__lsslauncher_on_update_fix_done?.()"
            )

    def uninstall_pack(self):
        # Maybe delete pack?
        dota_path = self._ensure_dota_path()
        if dota_path:
            delete_pack(dota_path)
            webview.windows[0].evaluate_js(
                f"window.__lsslauncher_on_delete_pack_done?.()"
            )
            self.state["installed_packs"] = []
            self._save_state()
            self._invalidate_cache()

    def cancel_download_pack(self, id: str):
        id = str(id)
        with self._download_lock:
            ev = self._download_cancel.get(id)
            if ev:
                ev.set()
        return True

    def download_pack(self, id: str):
        id = str(id)

        with self._download_lock:
            # если этот же id уже качается — не стартуем второй раз
            old = self._download_cancel.get(id)
            if old and not old.is_set():
                return

            ev = threading.Event()
            self._download_cancel[id] = ev

        def worker():
            try:
                status, file_info = self.api.get_file(int(id))
                if status != 200:
                    webview.windows[0].evaluate_js(
                        f"window.__lsslauncher_on_download_error?.('{id}', 'file info error')"
                    )
                    return

                name_file = get_uuid_file(id)
                download_url = file_info.get("download_url")
                md5 = file_info.get("md5")

                for p in self.api.download_file(
                    download_url, name_file, md5, stop_event=ev
                ):
                    if ev.is_set():
                        return
                    webview.windows[0].evaluate_js(
                        f"window.__lsslauncher_on_download_progress?.('{id}', {p})"
                    )

                if ev.is_set():
                    return

                webview.windows[0].evaluate_js(
                    f"window.__lsslauncher_on_download_done?.('{id}')"
                )
                if self.get_settings().get("soundEnabled"):
                    playsound(sound_path)
                self._invalidate_cache()

            except Exception as e:
                logger.error(f"Download pack failed: {e}")
                webview.windows[0].evaluate_js(
                    f"window.__lsslauncher_on_download_error?.('{id}', 'error')"
                )
            finally:
                with self._download_lock:
                    cur = self._download_cancel.get(id)
                    if cur is ev:
                        self._download_cancel.pop(id, None)

        threading.Thread(target=worker, daemon=True).start()

    def install_pack(self, id: str):
        dota_path = self._ensure_dota_path()
        if not dota_path:
            return

        try:
            name_file = get_uuid_file(id)
            install_pack_func(name_file, dota_path, self.api)

            installed = set(self.state.get("installed_packs", []))
            installed.add(str(id))
            self.state["installed_packs"] = list(installed)
            self._save_state()
            self._invalidate_cache()
            webview.windows[0].evaluate_js(f"window.__lsslauncher_on_install_done?.()")

        except FileNotFoundError:
            webview.windows[0].evaluate_js(
                f"window.__lsslauncher_set_modal?.(true, 'Установленная не верная директория Dota 2. Пожалуйста, проверьте путь в настройках.')"
            )
            logger.error(f"Pack file not found for installation: {id}")
        except Exception as e:
            logger.error(f"Install pack failed: {e}")

    def toggle_favorite(self, id: str, isFavorite: bool):
        favorites = set(self.state.get("favorites", []))
        if isFavorite:
            favorites.add(str(id))
        else:
            favorites.discard(str(id))

        self.state["favorites"] = list(favorites)
        self._save_state()
        self._invalidate_cache()

    def open_pack_screenshots(self, id: str):
        # Check if we can get URL from file info
        status, file_info = self.api.get_file(int(id))
        threading.Thread(
            target=lambda: webbrowser.open(
                file_info.get("screenshost", "https://t.me/screenshotsofpacks")
            ),
            daemon=True,
        ).start()

    def add_custom_pack(self):
        def worker():
            try:
                data_path = Path(APP_DATA_PATH)
                if not data_path.exists():
                    files = []
                else:
                    files = [
                        p.name
                        for p in data_path.iterdir()
                        if p.is_file() and p.name.lower().endswith(".vpk")
                    ]

                js_list = json.dumps(files)
                window = self._get_window()
                if window:
                    window.evaluate_js(
                        f"window.__lsslauncher_select_custom?.({js_list})"
                    )
            except Exception as e:
                logger.error(f"add_custom_pack failed: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def selected_custom(self, pack: str):
        # Install a custom pack selected from the packs folder
        dota_path = self._ensure_dota_path()
        if not dota_path:
            window = self._get_window()
            if window:
                window.evaluate_js(
                    "window.__lsslauncher_set_modal?.(true, 'Установленная не верная директория Dota 2. Пожалуйста, проверьте путь в настройках.')"
                )
            return {"ok": False, "error": "dota_path_not_found"}

        try:
            # `pack` is expected to be a filename (including extension) located in APP_DATA_PATH
            install_pack_func(pack, dota_path, self.api)

            installed = set(self.state.get("installed_packs", []))
            installed.add(str(pack))
            self.state["installed_packs"] = list(installed)
            self._save_state()
            self._invalidate_cache()
            return {"ok": True}
        except FileNotFoundError:
            window = self._get_window()
            if window:
                window.evaluate_js(
                    "window.__lsslauncher_set_modal?.(true, 'Установленная не верная директория Dota 2. Пожалуйста, проверьте путь в настройках.')"
                )
            logger.error(f"Selected custom pack file not found: {pack}")
            return {"ok": False, "error": "file_not_found"}
        except Exception as e:
            logger.error(f"selected_custom failed: {e}")
            return {"ok": False, "error": "exception", "message": str(e)}

    # =====================
    # SETTINGS
    # =====================
    def _extract_folder_path(self, payload: Any) -> Optional[str]:
        if isinstance(payload, str):
            value = payload.strip()
            return value or None

        if isinstance(payload, dict):
            # Frontends sometimes pass object payloads to pywebview API methods.
            for key in ("folder_path", "path", "dota_path"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def set_game_folder(self, folder_path: Any):
        normalized_path = self._extract_folder_path(folder_path)
        if not normalized_path:
            logger.error("empty_path")
            return {"ok": False, "error": "empty_path"}

        path = Path(normalized_path).expanduser()
        if not path.exists() or not path.is_dir():
            logger.error("invalid_path")
            return {"ok": False, "error": "invalid_path"}

        resolved = str(path.resolve())
        self.state["dota_path"] = resolved
        self._save_state()
        logger.success("resolved_path", resolved)
        return {"ok": True, "dota_path": resolved}

    def select_game_folder(self):
        try:
            window = self._get_window()
            if window is None:
                return {"ok": False, "error": "window_not_ready"}

            selected = window.create_file_dialog(webview.FileDialog.FOLDER)
            if not selected:
                return {"ok": False, "error": "cancelled"}

            # pywebview may return tuple/list depending on backend.
            selected_path = (
                selected[0] if isinstance(selected, (list, tuple)) else selected
            )
            print(selected_path)
            return {"ok": True, "path": selected_path}
        except Exception as e:
            logger.error(f"select_game_folder failed: {e}")
            return {"ok": False, "error": "dialog_error"}

    def on_change_sound(self, enabled: bool):
        self.state["sound_enabled"] = bool(enabled)
        self._save_state()
        return {"ok": True, "sound_enabled": self.state["sound_enabled"]}

    def save_settings(self, settings: Dict[str, Any]):
        if not isinstance(settings, dict):
            return {"ok": False, "error": "settings_must_be_object"}

        current = self.state.get("settings")
        if not isinstance(current, dict):
            current = {}

        current.update(settings)
        self.state["settings"] = current

        # Keep top-level keys synced when present in settings payload.
        if "dota_path" in settings and isinstance(settings["dota_path"], str):
            self.state["dota_path"] = settings["dota_path"]
        if "sound_enabled" in settings:
            self.state["sound_enabled"] = bool(settings["sound_enabled"])

        self._save_state()
        return {
            "ok": True,
            "settings": self.state["settings"],
            "dota_path": self.state.get("dota_path", ""),
            "sound_enabled": self.state.get("sound_enabled", True),
        }

    def get_settings(self):
        game_folder = self.state.get("dota_path") or self._ensure_dota_path() or ""
        sound_enabled = bool(self.state.get("sound_enabled", True))
        return {
            "gameFolder": game_folder,
            "soundEnabled": sound_enabled,
        }

    def _ensure_dota_path(self):
        path = self.state.get("dota_path")
        if not path:
            path = get_dota2_install_path()
            if path:
                self.state["dota_path"] = path
                self._save_state()
        return path

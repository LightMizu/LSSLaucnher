import gzip
import hashlib
import os
import shutil
import threading
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import requests
from loguru import logger

from utils.download import download
from utils.helpers import get_folder

APP_DATA_PATH = str(Path(get_folder()) / "packs")
URL = "https://lsslauncher.xyz"


class API:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        logger.info("API instance created")

    def get_token(self, login: str, password: str, hwid: str) -> int:
        """Sets the authorization token for the API class instance based on the server response using login and password. Return status code"""
        logger.info(f"Requesting token for user '{login}' with HWID '{hwid}'")

        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "username": login,
            "password": password,
            "hwid": hwid,
        }

        try:
            response = requests.post(
                f"{URL}/auth/token", headers=headers, data=data, timeout=10
            )
            logger.info(f"Token request returned status code {response.status_code}")
            response_json = response.json()
            if response.status_code == 200:
                self.token = f"{response_json['token_type'].capitalize()} {response_json['access_token']}"
                logger.success("Token successfully obtained")
                return 200
        except requests.RequestException as e:
            logger.error(f"Token request failed: {e}")
            return 0

        if response_json.get("detail") == "Incorrect username or password":
            return 401
        elif response_json.get("detail", "") == "Invalid HWID":
            return 409
        return response.status_code

    def get_me(self, hwid: str) -> Tuple[int, dict]:
        """Retrieves user information and returns a tuple containing the status code and the JSON response."""
        logger.info(f"Fetching user info for HWID '{hwid}'")
        headers = {
            "accept": "application/json",
            "Authorization": self.token,
            "x-hwid": f"{hwid}",
        }

        try:
            response = requests.get(f"{URL}/users/me", headers=headers)
            logger.info(
                f"User info request returned status code {response.status_code}"
            )
            return response.status_code, response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user info: {e}")
            return 0, {}

    def get_files(self, skip, limit) -> Tuple[int, List[dict]]:
        logger.info(f"Fetching files list with skip={skip} and limit={limit}")
        headers = {
            "accept": "application/json",
            "Authorization": self.token,
        }

        param = {
            "skip": skip,
            "limit": limit,
        }

        try:
            response = requests.get(f"{URL}/files/", headers=headers, params=param)
            logger.info(
                f"Files list request returned status code {response.status_code}"
            )
            return response.status_code, response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch files list: {e}")
            return 0, []

    def get_file(self, id_file: int) -> Tuple[int, dict]:
        logger.info(f"Fetching file info for file ID {id_file}")
        headers = {
            "accept": "application/json",
            "Authorization": self.token,
        }

        try:
            response = requests.get(f"{URL}/files/{id_file}", headers=headers)
            logger.info(
                f"File info request returned status code {response.status_code}"
            )
            return response.status_code, response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch file info: {e}")
            return 0, {}

    def download_file(
        self, url, name, hash_file, stop_event: threading.Event | None = None
    ) -> Iterator[float]:
        logger.info(f"Starting download for file '{name}'")

        os.makedirs(APP_DATA_PATH, exist_ok=True)
        local_filename = Path(APP_DATA_PATH) / name
        gz_path = Path(f"{local_filename}.gz")

        # Check local file
        if os.path.isfile(local_filename):
            if hash_file:
                logger.info(f"Checking hash for existing file '{local_filename}'")
                md5_local = hashlib.md5()
                with open(local_filename, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        md5_local.update(chunk)
                md5_local_hex = md5_local.hexdigest()
                if md5_local_hex == hash_file:
                    logger.info("Local file hash matches, skipping download")
                    return
                else:
                    logger.warning("Local file hash does not match, re-downloading")
            else:
                logger.info("Local file exists, skipping download")
                return

        # Если уже есть старый .gz от прошлой попытки — лучше убрать
        if gz_path.exists():
            try:
                gz_path.unlink()
            except Exception as e:
                logger.warning(f"Could not remove stale gz '{gz_path}': {e}")

        # ✅ ВАЖНО: передаём stop_event внутрь download()
        for i in download(url, str(gz_path), stop_event=stop_event):
            if stop_event and stop_event.is_set():
                # cleanup partial gz
                try:
                    if gz_path.exists():
                        gz_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not remove partial gz '{gz_path}': {e}")
                return
            yield i

        # на всякий случай — если отменили между окончанием и распаковкой
        if stop_event and stop_event.is_set():
            try:
                if gz_path.exists():
                    gz_path.unlink()
            except Exception as e:
                logger.warning(f"Could not remove partial gz '{gz_path}': {e}")
            return

        logger.info(f"Extracting downloaded gzip file '{gz_path}'")

        try:
            with gzip.open(gz_path, "rb") as f_in:
                with open(local_filename, "wb") as f_out:
                    # Можно добавить проверку отмены во время распаковки (редко нужно, но приятно)
                    while True:
                        if stop_event and stop_event.is_set():
                            raise RuntimeError("cancelled")
                        chunk = f_in.read(1024 * 1024)
                        if not chunk:
                            break
                        f_out.write(chunk)

            gz_path.unlink(missing_ok=True)
            logger.success(f"File '{name}' downloaded and extracted successfully")

        except Exception as e:
            # если отменили или распаковка упала — чистим хвосты
            logger.warning(f"Extract failed for '{gz_path}': {e}")
            try:
                if local_filename.exists():
                    local_filename.unlink()
            except Exception:
                pass
            try:
                if gz_path.exists():
                    gz_path.unlink()
            except Exception:
                pass
            # пробрасывать ошибку или просто return — как тебе нужно
            return

    def merge_pack(self, s3_key_main: str, s3_key_second: str):
        logger.info(f"Add task merge {s3_key_main} {s3_key_second}")
        headers = {
            "accept": "application/json",
            "Authorization": self.token,
        }
        data = {"first_key": s3_key_main, "second_key": s3_key_second}
        try:
            response = requests.post(f"{URL}/files/merge", headers=headers, json=data)
            logger.info(
                f"Task merge added returned status code {response.status_code} with task_id {response.json()}"
            )
            return response.status_code, response.json()["id"]
        except requests.RequestException as e:
            logger.error(f"Failed to add task: {e}")
            return 0, ""

    def get_task_status(self, task_id) -> Tuple[int, dict]:
        logger.info(f"Getting status task {task_id}")
        headers = {
            "accept": "application/json",
            "Authorization": self.token,
        }
        try:
            response = requests.get(f"{URL}/task/{task_id}", headers=headers)
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f" Failed to get task {e}")
            return 0, {}

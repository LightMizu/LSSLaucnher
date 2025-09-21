import hashlib
import os
import requests
import shutil
from tkinter import ttk
import tempfile
import tkinter as tk
import subprocess
from tkinter import messagebox
import sys
import aiohttp
import asyncio 
from typing import Iterator, AsyncGenerator
import threading
import traceback

async def fetch_chunk(session, url, start, end, part_file, progress_queue):
    headers = {"Range": f"bytes={start}-{end}"}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        dowloaded = 0
        with open(part_file, "wb") as f:
            while True:
                chunk = await resp.content.read(1024*256)  # 1 MB
                if not chunk:
                    break
                f.write(chunk)
                dowloaded += len(chunk)
    return dowloaded  # сообщаем о прогрессе

async def download_file_fast(url: str, filename: str, part_size: int = 1024*1024) -> AsyncGenerator[float, None]:
    """
    Асинхронно качает файл с прогрессом.

    Yields:
        float: прогресс в процентах (0–100)
    """
    #Получаем размер файла
    


    timeout = aiohttp.ClientTimeout(total=None, sock_connect=60, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        headers = {"Range": f"bytes={1}-{2}"}
        async with session.get(url, headers=headers) as resp:
            file_size = int(resp.headers["Content-Range"].split("/")[1])
        # многопоточная загрузка
        ranges = []
        parts = (file_size // part_size)+1
        for i in range(parts):
            start = i * part_size
            end = file_size - 1 if i == parts - 1 else (start + part_size - 1)
            ranges.append((start, end))
        # очередь для прогресса
        progress_queue = asyncio.Queue()
        part_files = []
        tasks = []
        for i, (start, end) in enumerate(ranges):
            part_file = f"{filename}.part{i}"
            part_files.append(part_file)
            tasks.append(fetch_chunk(session, url, start, end, part_file, progress_queue))

        
        # запускаем скачивание
        # отслеживаем прогресс
        done = 0
        for future in asyncio.as_completed(tasks):
            downloaded = await future
            done += downloaded
            yield done/file_size*100

        # склеиваем файл
        with open(filename, "wb") as f:
            for part_file in part_files:
                with open(part_file, "rb") as pf:
                    f.write(pf.read())
                os.remove(part_file)

        yield 100.0  # финальный прогресс
                
def download(url: str, filename: str) -> Iterator[float]:
    """
    Синхронный генератор, использующий асинхронную download_file_fast.
    """
    async def run():
        async for progress in download_file_fast(url, filename):
            yield progress

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agen = run()

    try:
        while True:
            yield loop.run_until_complete(agen.__anext__())
    except StopAsyncIteration:
        pass
    finally:
        loop.close()


def resource_path(relative_path):
    # Получаем абсолютный путь к ресурсам.
    try:
        # PyInstaller создает временную папку в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

APP_NAME = "lsslauncher.exe"  # имя основного exe
UPDATE_URL = "https://lsslauncher.xyz/build"         # ссылка на exe
HASH_URL = "https://lsslauncher.xyz/sha256"    # ссылка на sha256



class UpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.iconbitmap(resource_path('build_assets/setup.ico'))
        self.root.title("Проверка обновлений")
        self.root.geometry("400x120")
        self.root.resizable(False, False)

        self.status = tk.Label(root, text="Проверка обновлений...", font=("Arial", 12))
        self.status.pack(pady=10)

        self.progress_bar = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress_bar.pack(pady=10)

        # запускаем обновление сразу
        self.root.after(100, self.update_app)

    @staticmethod
    def sha256sum(file_path):
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def get_remote_hash():
        resp = requests.get(HASH_URL, timeout=10)
        resp.raise_for_status()
        return resp.text.strip()

    def download_with_progress(self, url, dest):
        for progress in download(url ,dest):
            print(progress, dest)
            percent = progress
            self.progress_bar["value"] = percent
            self.root.update_idletasks()
    
    def check_dowload(self):
        if self.thread.is_alive():
            # Если поток ещё работает, проверяем снова через 100 мс
            self.root.after(100, self.check_dowload)
        else:
            self.after_dowload()
    
    def after_dowload(self):
        new_hash = self.sha256sum(self.tmp_file)
        if new_hash != self.remote_hash:
            messagebox.showerror("Ошибка", "Хеш скачанного файла не совпадает!")
            os.remove(self.tmp_file)
            subprocess.Popen(["lsslauncher.exe"])
            self.root.quit()
            return
        if os.path.exists(self.local_exe):
            os.remove(self.local_exe)

        shutil.move(self.tmp_file, self.local_exe)
        shutil.rmtree(self.temp_dir)
        subprocess.Popen(["lsslauncher.exe"])
        self.root.quit()
    
    def update_app(self):
        try:
            self.status.config(text="Проверка обновлений...")
            self.local_exe = os.path.join(os.getcwd(), APP_NAME)
            self.remote_hash = self.get_remote_hash()

            # проверяем локальный файл
            if os.path.exists(self.local_exe):
                self.local_hash = self.sha256sum(self.local_exe)
                if self.local_hash == self.remote_hash:
                    subprocess.Popen(["lsslauncher.exe"])
                    self.root.quit()
                    return
            self.status.config(text= "Обновление")
            # качаем новый exe
            self.temp_dir = tempfile.mkdtemp()
            self.tmp_file = os.path.join(self.temp_dir,'lsslauncher.exe')
            self.thread = threading.Thread(target = lambda: self.download_with_progress(UPDATE_URL, self.tmp_file))
            self.thread.start()
            self.check_dowload()
            # проверим хеш
            
        except Exception as e:
            trace = traceback.format_exc()
            messagebox.showerror("Ошибка", f"Не удалось обновить:\n{e}\n{trace}")


def main():
    root = tk.Tk()
    app = UpdaterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import aiohttp
import asyncio 
from typing import Iterator, AsyncGenerator
import os
from loguru import logger
from tempfile import mkdtemp

async def fetch_chunk(session, url, start, end, part_file, progress_queue):
    logger.info(f"Start fetching {url} from {start} to {end} part file {part_file}")
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

async def download_file_fast(url: str, filename: str, part_size: int = 1024*1024*10) -> AsyncGenerator[float, None]:
    """
    Асинхронно качает файл с прогрессом.

    Yields:
        float: прогресс в процентах (0–100)
    """
    logger.info(f"Start dowload {url} in {filename} with part size {part_size} B")
    
    

    
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=60, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        #Получаем размер файла
        headers = {"Range": "bytes=0-1"}
        async with session.get(url, headers=headers) as resp:
            file_size = int(resp.headers["Content-Range"].split("/")[1])
        logger.info(f"Get file_size: {file_size} KB")
        # многопоточная загрузка
        ranges = []
        parts = (file_size // part_size)+1
        logger.info(f"Spliting file on {parts} part")
        for i in range(parts):
            
            start = i * part_size
            end = file_size - 1 if i == parts - 1 else (start + part_size - 1)
            logger.info(f"Part {len(ranges)+1}: {start}-{end}")
            ranges.append((start, end))
        # очередь для прогресса
        progress_queue = asyncio.Queue()
        part_files = []
        tasks = []
        logger.info("Creating tempdir")
        temp_dir = mkdtemp(prefix="lss")
        logger.info(f"Create temdir {temp_dir}")
        basename = os.path.basename(filename)
        for i, (start, end) in enumerate(ranges):
            part_file = os.path.join(temp_dir,f"{basename}.part{i}")
            part_files.append(part_file)
            tasks.append(fetch_chunk(session, url, start, end, part_file, progress_queue))

        
        # запускаем скачивание
        # отслеживаем прогресс
        done = 0
        for future in asyncio.as_completed(tasks):
            downloaded = await future
            done += downloaded
            logger.info(f"Total downloaded {downloaded} B")
            yield done/file_size*100

        # склеиваем файл
        logger.info("Start join parts")
        with open(filename, "wb") as f:
            for part_file in part_files:
                with open(part_file, "rb") as pf:
                    f.write(pf.read())
                logger.info(f"Joined part {os.path.basename(part_file)}")
                os.remove(part_file)
                logger.info(f"Removed part {os.path.basename(part_file)}")
        logger.info("Removed tempdir")
        yield 100.0  # финальный прогресс
                
def download(url: str, filename: str) -> Iterator[float]:
    """
    Синхронный генератор, использующий асинхронную download_file_fast
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
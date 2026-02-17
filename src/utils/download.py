import aiohttp
from aiohttp import ClientPayloadError
import asyncio 
from typing import Iterator, AsyncGenerator
import os
from loguru import logger
from tempfile import mkdtemp
import shutil

async def fetch_chunk(session, url, start, end, part_file, retry:int=5):
    logger.info(f"Start fetching {url} from {start} to {end} part file {part_file} retry count {retry}")
    headers = {"Range": f"bytes={start}-{end}"}
    if retry == 0:
        return 0
    try:
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
    except ClientPayloadError:
        logger.warning("ClientPayloadError retrying...")
        return await fetch_chunk(session, url, start, end, part_file, retry-1)
    return dowloaded  # сообщаем о прогрессе

async def download_file_single(url: str, filename: str) -> AsyncGenerator[float, None]:
    logger.info(f"Starting single-threaded download for {url}")
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=60, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            file_size = int(resp.headers.get("Content-Length", 0))
            logger.info(f"File size: {file_size}")
            
            downloaded = 0
            with open(filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if file_size > 0:
                        yield downloaded / file_size * 100
                    else:
                        yield 0.0

async def download_file_fast(url: str, filename: str, part_size: int = 1024*1024*10) -> AsyncGenerator[float, None]:
    """
    Асинхронно качает файл с прогрессом.
    Пытается скачать многопоточно, если не выходит - однопоточно.
    """
    logger.info(f"Start download {url} in {filename} with part size {part_size} B")
    
    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=60, sock_read=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Получаем размер файла и проверяем поддержку Range
            headers = {"Range": "bytes=0-1"}
            async with session.get(url, headers=headers) as resp:
                if resp.status != 206: # Partial Content
                     raise ValueError("Server does not support Range requests")
                content_range = resp.headers.get("Content-Range")
                if not content_range:
                     raise ValueError("No Content-Range header")
                file_size = int(content_range.split("/")[1])
            
            logger.info(f"Get file_size: {file_size} B")
            
            # многопоточная загрузка
            ranges = []
            parts = (file_size // part_size) + 1
            logger.info(f"Splitting file on {parts} phases")
            for i in range(parts):
                start = i * part_size
                end = file_size - 1 if i == parts - 1 else (start + part_size - 1)
                logger.info(f"Part {len(ranges)+1}: {start}-{end}")
                ranges.append((start, end))
            
            part_files = []
            tasks = []
            logger.info("Creating tempdir")
            temp_dir = mkdtemp(prefix="lss")
            logger.info(f"Create temdir {temp_dir}")
            basename = os.path.basename(filename)
            for i, (start, end) in enumerate(ranges):
                part_file = os.path.join(temp_dir, f"{basename}.part{i}")
                part_files.append(part_file)
                tasks.append(fetch_chunk(session, url, start, end, part_file))

            done = 0
            for future in asyncio.as_completed(tasks):
                downloaded_chunk = await future
                done += downloaded_chunk
                logger.info(f"Total downloaded {done} B")
                yield done / file_size * 100

            # склеиваем файл
            logger.info("Start join parts")
            with open(filename, "wb") as f:
                for part_file in part_files:
                    with open(part_file, "rb") as pf:
                        f.write(pf.read())
                    os.remove(part_file)
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info("Removed tempdir")
            yield 100.0

    except Exception as e:
        logger.warning(f"Multi-threaded download failed: {e}. Falling back to single-threaded.")
        async for progress in download_file_single(url, filename):
             yield progress

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
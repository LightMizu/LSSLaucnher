import asyncio
import os
import shutil
import threading
from tempfile import mkdtemp
from typing import AsyncGenerator, Iterator, Optional, Union

import aiohttp
from aiohttp import ClientPayloadError
from loguru import logger

StopEvent = Union[threading.Event, asyncio.Event]


def _is_stopped(stop_event: Optional[StopEvent]) -> bool:
    try:
        return bool(stop_event) and stop_event.is_set()
    except Exception:
        return False


async def fetch_chunk(
    session,
    url,
    start,
    end,
    part_file,
    retry: int = 5,
    stop_event: Optional[StopEvent] = None,
):
    logger.info(
        f"Start fetching {url} from {start} to {end} part file {part_file} retry count {retry}"
    )

    if _is_stopped(stop_event):
        return 0

    headers = {"Range": f"bytes={start}-{end}"}
    if retry == 0:
        return 0

    try:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            downloaded = 0
            with open(part_file, "wb") as f:
                while True:
                    if _is_stopped(stop_event):
                        # досрочно выходим — файл part останется неполным, его удалим выше при cleanup
                        return downloaded

                    chunk = await resp.content.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

    except ClientPayloadError:
        logger.warning("ClientPayloadError retrying...")
        return await fetch_chunk(
            session, url, start, end, part_file, retry - 1, stop_event=stop_event
        )

    return downloaded


async def download_file_single(
    url: str, filename: str, stop_event: Optional[StopEvent] = None
) -> AsyncGenerator[float, None]:
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
                    if _is_stopped(stop_event):
                        return
                    f.write(chunk)
                    downloaded += len(chunk)

                    if file_size > 0:
                        yield downloaded / file_size * 100
                    else:
                        yield 0.0


async def download_file_fast(
    url: str,
    filename: str,
    part_size: int = 1024 * 1024 * 10,
    stop_event: Optional[StopEvent] = None,
    delete_partial_on_cancel: bool = True,
) -> AsyncGenerator[float, None]:
    """
    Асинхронно качает файл с прогрессом.
    Пытается скачать многопоточно, если не выходит - однопоточно.
    Поддерживает stop_event.
    """
    logger.info(f"Start download {url} in {filename} with part size {part_size} B")

    if _is_stopped(stop_event):
        return

    temp_dir = None
    part_files: list[str] = []

    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=60, sock_read=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Получаем размер файла и проверяем поддержку Range
            headers = {"Range": "bytes=0-1"}
            async with session.get(url, headers=headers) as resp:
                if resp.status != 206:
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
                ranges.append((start, end))

            logger.info("Creating tempdir")
            temp_dir = mkdtemp(prefix="lss")
            logger.info(f"Create temdir {temp_dir}")
            basename = os.path.basename(filename)

            tasks: list[asyncio.Task] = []
            for i, (start, end) in enumerate(ranges):
                part_file = os.path.join(temp_dir, f"{basename}.part{i}")
                part_files.append(part_file)
                tasks.append(
                    asyncio.create_task(
                        fetch_chunk(
                            session, url, start, end, part_file, stop_event=stop_event
                        )
                    )
                )

            done = 0
            try:
                for fut in asyncio.as_completed(tasks):
                    if _is_stopped(stop_event):
                        # отменяем все оставшиеся
                        for t in tasks:
                            t.cancel()
                        raise asyncio.CancelledError()

                    downloaded_chunk = await fut
                    done += downloaded_chunk
                    yield done / file_size * 100
            finally:
                # если что-то осталось — добиваем отменой
                if _is_stopped(stop_event):
                    for t in tasks:
                        t.cancel()

            if _is_stopped(stop_event):
                raise asyncio.CancelledError()

            # склеиваем файл
            logger.info("Start join parts")
            with open(filename, "wb") as f:
                for part_file in part_files:
                    with open(part_file, "rb") as pf:
                        f.write(pf.read())

            yield 100.0

    except asyncio.CancelledError:
        logger.info("Download cancelled by stop_event")
        # просто выходим — cleanup в finally
        return

    except Exception as e:
        logger.warning(
            f"Multi-threaded download failed: {e}. Falling back to single-threaded."
        )
        # fallback single-threaded тоже должен уметь останавливаться
        async for progress in download_file_single(
            url, filename, stop_event=stop_event
        ):
            yield progress

    finally:
        # cleanup temp parts
        try:
            for pf in part_files:
                try:
                    if os.path.exists(pf):
                        os.remove(pf)
                except Exception:
                    pass
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

        # удалить недокачанный файл при отмене
        if delete_partial_on_cancel and _is_stopped(stop_event):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception:
                pass


def download(
    url: str, filename: str, stop_event: Optional[StopEvent] = None
) -> Iterator[float]:
    """
    Синхронный генератор, использующий асинхронную download_file_fast
    """

    async def run():
        async for progress in download_file_fast(url, filename, stop_event=stop_event):
            yield progress

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agen = run()

    try:
        while True:
            if _is_stopped(stop_event):
                break
            yield loop.run_until_complete(agen.__anext__())
    except StopAsyncIteration:
        pass
    finally:
        loop.close()

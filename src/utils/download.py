import aiohttp
import asyncio 

async def download_file(url: str, filename: str, chunk_size: int = 1024*1024):
    """
    Скачивает файл асинхронно с указанным размером блока.

    Args:
        url (str): Ссылка на файл.
        filename (str): Имя файла для сохранения.
        chunk_size (int, optional): Размер блока в байтах. По умолчанию 1 МБ.
    """
    timeout = aiohttp.ClientTimeout(
        sock_connect=60,  # до 60 сек на соединение
        sock_read=None,   # без ограничения на чтение (ждём сколько надо)
        total=None        # тоже без общего ограничения
    )
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            with open(filename, "wb") as f:
                while True:
                    chunk = await resp.content.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
def download(url: str,file: str):
    asyncio.run(download_file(url, file))
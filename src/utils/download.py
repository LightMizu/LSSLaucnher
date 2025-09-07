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
    async with aiohttp.ClientSession() as session:
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
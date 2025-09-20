import flet as ft
from app import Launcher
from pathlib import Path
from utils.helpers import get_folder
from utils.logging2loguru import InterceptHandler
from loguru import logger
import logging

log_dir = "logs"
Path(log_dir).mkdir(exist_ok=True)
logger.add(
    "logs/launcher.log",
    rotation="1 day",
    retention=7,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan> | {message}"
)

logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
# Remove default handlers and redirect everything

@logger.catch
def main(page: ft.Page):
    logger.info("Starting app...")
    app = Launcher(page)
    app.run()

if __name__ == '__main__':
    
    (Path(get_folder())/"packs").mkdir(exist_ok=True,parents=True)
    ft.app(target=main, assets_dir='assets')
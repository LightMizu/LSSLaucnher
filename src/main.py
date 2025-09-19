import flet as ft
from app import Launcher
from pathlib import Path
from utils.helpers import get_folder

def main(page: ft.Page):
    app = Launcher(page)
    app.run()

if __name__ == '__main__':
    (Path(get_folder())/"packs").mkdir(exist_ok=True,parents=True)
    ft.app(target=main, assets_dir='assets')
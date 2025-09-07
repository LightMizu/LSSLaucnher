import flet as ft
from src.launcher.app import Laucher
from pathlib import Path

ASSETS = Path(__file__).resolve().parent /"src"/"launcher"/ "assets" 
ICON_PATH = (ASSETS / "icon.ico").resolve()
def main(page: ft.Page):
    app = Laucher(page)
    app.run()
print(ASSETS)
if __name__ == '__main__':
    ft.app(target=main, assets_dir=str(ASSETS) )
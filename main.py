import flet as ft
from src.app import Launcher
from pathlib import Path


def main(page: ft.Page):
    app = Launcher(page)
    app.run()

if __name__ == '__main__':
    ft.app(target=main)
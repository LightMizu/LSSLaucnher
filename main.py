import flet as ft
from src.launcher.app import Laucher


def main(page: ft.Page):
    app = Laucher(page)
    app.run()

if __name__ == "__main__":
    ft.app(target=main)
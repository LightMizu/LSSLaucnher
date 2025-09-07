import flet as ft

from .screen import Screen


class AboutScreen(Screen):
    def __init__(self, navigator):
        self.navigator = navigator

    def on_resize(self, e):
        pass

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Создатели:", size=30, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.TextButton("Darkness", url='https://t.me/Darkness_Logovo'),
                            ft.TextButton("Light", url='https://t.me/removed_person'),
                            ft.TextButton("Lssqqqq", url='https://t.me/lssqqqq'),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True,
                        expand_loose=True
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )

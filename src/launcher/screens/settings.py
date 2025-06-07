from .screen import Screen
import flet as ft

class SettingsScreen(Screen):
    def __init__(self, navigator):
        self.navigator = navigator

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Settings Screen", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("Configure your app settings here.", size=20),
                    ft.ElevatedButton(
                        "Back to Home",
                        on_click=lambda e: self.navigator.navigate_to("home")
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )






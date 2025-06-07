from .navigator import Navigator
import flet as ft
from typing import Dict
from src.launcher.screens import Screen

class ScreenManager(Navigator):
    def __init__(self, page: ft.Page):
        self.page = page
        self.screens: Dict[str, Screen] = {}
        self.main_container = ft.Container(expand=True)

    def add_screen(self, name: str, screen: Screen):
        self.screens[name] = screen

    def navigate_to(self, screen_name: str):
        if screen_name in self.screens:
            self.main_container.content = self.screens[screen_name].build()
            self.page.update()
        else:
            print(self.screens)
            print(f"Screen {screen_name} not found")

    def get_main_container(self) -> ft.Container:
        return self.main_container
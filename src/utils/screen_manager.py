from .navigator import Navigator
import flet as ft
from typing import Dict
from screens.screen import Screen

class ScreenManager(Navigator):
    def __init__(self, page: ft.Page):
        self.page = page
        self.screens: Dict[str, Screen] = {}
        self.main_container = ft.Container(expand=True)

    def add_screen(self, name: str, screen: Screen):
        self.screens[name] = screen

    def navigate_to(self, screen_name: str):
        if screen_name in self.screens:
            screen = self.screens[screen_name]
            self.main_container.content = screen.build()
            self.page.on_resized = screen.on_resize
            self.page.update()
        else:
            print(f'Screen {screen_name} not found')

    def get_main_container(self) -> ft.Container:
        return self.main_container
import flet as ft

from .screen import Screen

from utils import API

class MergeScreen(Screen):
    def __init__(self, navigator, api: API):
        self.navigator = navigator
        self.merge_button = ft.Button("Совместить", height=60, width=300)
        status_code, self.file_list = api.get_files(0,100)
        self.dropdown_options = []
        for pack in self.file_list:
            self.dropdown_options.append(ft.dropdown.DropdownOption(key=pack["s3_key"], text=pack["name"]))
        self.action_button = self.merge_button
        self.container: ft.Container = ft.Container(
            content=ft.Column(
                [
                    ft.Column(
                        [
                            ft.Dropdown(options=self.dropdown_options),
                            ft.Icon(name=ft.Icons.ADD_ROUNDED),
                            ft.Dropdown(options=self.dropdown_options),
                            self.action_button
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
    def on_resize(self, e) -> None:
        pass

    def build(self) -> ft.Container:
        return self.container
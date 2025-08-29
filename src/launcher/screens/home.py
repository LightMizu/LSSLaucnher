import flet as ft
from .screen import Screen
from src.launcher.utils.api import API
from src.launcher.utils.helpers import find_by_key, get_uuid_file
from src.launcher.utils.install_pack import install_pack

class PackCard(ft.Container):
    def __init__(self, file: dict, select_button: ft.Control):
        super().__init__(
            content=ft.SafeArea(
                ft.Row(
                    [
                        ft.Text(file['name']),
                        ft.FilledButton('Скрины', url=file['screenshost']),
                        select_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                minimum_padding=20,
            ),
            height=75,
            bgcolor=ft.Colors.ON_SECONDARY,
            border_radius=20,
        )
        self.select_button = select_button

class HomeScreen(Screen):
    def __init__(self, navigator, api: API):
        self.navigator = navigator
        self.api: API = api
        self.selected_pack = -1
        status_code, self.files = api.get_files(0, 100)

    def build(self) -> ft.Container:
        self.list_files = []
        for file in self.files:

            select_button = ft.IconButton(
                                    ft.Icons.CIRCLE_OUTLINED,
                                )
            select_button.on_click = lambda e: self.navigator.page.run_thread(self.select_pack, file['id'], select_button)

            self.list_files.append(
                PackCard(file, select_button)
            )
        self.packs_column = ft.SafeArea(
            ft.Column(
                self.list_files,
                width=self.navigator.page.width - 355,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            minimum_padding=20,
        )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.OutlinedButton(text='Запустить игру', height=50, width=200),
                            ft.OutlinedButton(text='Установить', height=50, width=200),
                            ft.OutlinedButton(
                                text='Пофиксить VAC', height=50, width=200
                            ),
                            ft.OutlinedButton(text='Удалить', height=50, width=200),
                            ft.Image('assets/logo.png', height=200, width=200),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=300,
                    ),
                    ft.VerticalDivider(width=5, color=ft.Colors.PRIMARY),
                    self.packs_column,
                ]
            ),
            alignment=ft.alignment.center,
        )

    def on_resize(self, e):
        self.packs_column.width = self.navigator.page.width - 335
        self.navigator.page.update()

    def select_pack(self, id_pack: int, button: ft.IconButton):
        for card in self.list_files:
            card.select_button.icon = ft.Icons.CIRCLE_OUTLINED
        self.selected_pack = id_pack
        parent = button.parent
        parent.select_button = ft.ProgressRing()
        self.navigator.page.update()
        file = find_by_key(self.files, 'id', id_pack)
        self.api.download_file(file['download_url'], get_uuid_file(file['s3_file']))
        button.icon = ft.Icons.CIRCLE_ROUNDED
        parent.select_button = button
        self.navigator.page.update()
    
    def install_pack(self, e):
        id_pack = self.select_pack
        file = find_by_key(self.files, 'id', id_pack)
        uuid = get_uuid_file(file['s3_key']) 
        install_pack(uuid)
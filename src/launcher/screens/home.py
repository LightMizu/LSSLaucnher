import flet as ft
from .screen import Screen
from src.launcher.utils.api import API
from src.launcher.utils.helpers import find_by_key, get_uuid_file
from src.launcher.utils.install_pack import install_pack, launch_dota, delete_pack


class PackCard(ft.Container):
    def __init__(self, file: dict, select_button: ft.Control):
        self.select_button = select_button
        self.progress_ring = ft.ProgressRing(width=20, height=20, visible=False)
        super().__init__(
            content=ft.SafeArea(
                ft.Row(
                    [
                        ft.Text(file['name']),
                        ft.FilledButton('Скрины', url=file['screenshost']),
                        self.select_button,
                        self.progress_ring,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                minimum_padding=20,
            ),
            height=75,
            bgcolor=ft.Colors.ON_SECONDARY,
            border_radius=20,
        )
        

class HomeScreen(Screen):
    def __init__(self, navigator, api: API):
        self.navigator = navigator
        self.api: API = api
        self.selected_pack = -1
        status_code, self.files = api.get_files(0, 100)

    def build(self) -> ft.Container:
        self.list_files = []

        for file in self.files:
            select_button = ft.IconButton(ft.Icons.CIRCLE_OUTLINED)

            # Создаём функцию-обёртку, чтобы замыкание работало правильно
            def on_click_factory(f=file, btn=select_button):
                def on_click(e):
                    self.select_pack(f['id'], btn)
                return on_click

            select_button.on_click = on_click_factory()

            self.list_files.append(PackCard(file, select_button))

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
                            ft.OutlinedButton(text='Запустить игру', height=50, width=200, on_click=self.launch),
                            ft.OutlinedButton(text='Установить', height=50, width=200, on_click=self.install_pack_handler),
                            ft.OutlinedButton(
                                text='Пофиксить VAC', height=50, width=200
                            ),
                            ft.OutlinedButton(text='Удалить', height=50, width=200, on_click=self.delete_pack),
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
        card = next(c for c in self.list_files if c.select_button == button)
        # Меняем кнопку на ProgressRing для выбранного pack
        card.progress_ring.value = None
        card.progress_ring.visible = True
        card.select_button.visible = False
        self.navigator.page.update()
        # Находим файл
        file = find_by_key(self.files, 'id', id_pack)
        #получаем uuid 
        name_file = get_uuid_file(file['id'])
        # Скачиваем файл
        for downloaded, total in self.api.download_file(file['download_url'], name_file, file['md5']):
            card.progress_ring.value = downloaded/total
            self.navigator.page.update()
        card.progress_ring.visible = False
        card.select_button.visible = True
        # Сбрасываем иконки у всех карточек
        for i, card in enumerate(self.list_files):
            card.select_button.icon = ft.Icons.CIRCLE_OUTLINED
            
        # После загрузки ставим выбранную иконку
        button.icon = ft.Icons.CIRCLE_ROUNDED
        # Отмечаем выбранный pack
        self.selected_pack = id_pack
        self.navigator.page.update()

    def launch(self, e):
        launch_dota()

    def delete_pack(self, e:ft.ControlEventType):
        e.control.text = "Удаление..."
        self.navigator.page.update()
        delete_pack(self.navigator.page.client_storage.get('lsslaucher.dota_path'), self.api)
        e.control.text = "Удалить"
        self.navigator.page.update()

    def install_pack_handler(self, e):
        e.control.text = "Установка..."
        self.navigator.page.update()
        id_pack = self.selected_pack
        
        if id_pack == -1:
            print("Пак не выбран")
            return
        name_file = get_uuid_file(id_pack)
        install_pack(name_file, self.navigator.page.client_storage.get('lsslaucher.dota_path'), self.api)
        e.control.text = "Установить"
        self.navigator.page.update()
from .screen import Screen
import flet as ft
from launcher.utils.install_pack import get_dota2_install_path

class SettingsScreen(Screen):
    def __init__(self, navigator):
        self.navigator = navigator
        self.folder_picker = None
        self.selected_path = ft.Text('Папка не выбрана', size=16)
        if self.navigator.page.client_storage.contains_key('lsslaucher.dota_path'):
            self.selected_path.value = self.navigator.page.client_storage.get('lsslaucher.dota_path')
        else:
            path = get_dota2_install_path()
            self.selected_path.value = path
            self.navigator.page.client_storage.set('lsslaucher.dota_path', path)
        self.folder_picker = ft.FilePicker(on_result=self.on_pick_result)
        self.navigator.page.overlay.append(self.folder_picker)

    def on_resize(self, e):
        pass

    def on_pick_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.selected_path.value = e.path
            self.navigator.page.client_storage.set('lsslaucher.dota_path', e.path)
            self.navigator.page.update()

    def build(self) -> ft.Container:
        # создаём FilePicker один раз и добавляем в overlay

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text('Путь к папке dota', scale=1.6),
                    ft.Row(
                        [
                            ft.Container(
                                self.selected_path,
                                border_radius=50,
                                padding=10,
                                border=ft.border.all(
                                    3, ft.Colors.ON_SECONDARY_CONTAINER
                                ),
                            ),
                            # Кнопка выбора папки
                            ft.ElevatedButton(
                                'Выбрать папку',
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=lambda _: (
                                    self.folder_picker.get_directory_path()
                                    if self.folder_picker
                                    else None
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=30,
        )

from .screen import Screen
import flet as ft


class SettingsScreen(Screen):
    def __init__(self, navigator):
        self.navigator = navigator
        self.folder_picker = None
        self.selected_path = ft.Text(size=16)

        self.selected_path.value = self.navigator.page.client_storage.get(
            "lsslaucher.dota_path"
        )
        if self.selected_path.value == "":
            self.selected_path.value = "Папка не выбрана"
        self.folder_picker = ft.FilePicker(on_result=self.on_pick_result)
        self.navigator.page.overlay.append(self.folder_picker)

    def on_resize(self, e):
        pass

    def on_pick_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.selected_path.value = e.path
            self.navigator.page.client_storage.set("lsslaucher.dota_path", e.path)
            self.navigator.page.update()

    def build(self) -> ft.Container:
        # создаём FilePicker один раз и добавляем в overlay

        return ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Путь к папке dota", size=30),
                        ft.Row(
                            [
                                ft.Container(
                                    self.selected_path,
                                    border_radius=50,
                                    padding=ft.Padding(10, 2, 10, 2),
                                    height=40,
                                    alignment=ft.alignment.center,
                                    border=ft.border.all(
                                        2, ft.Colors.ON_SECONDARY_CONTAINER
                                    ),
                                ),
                                # Кнопка выбора папки
                                ft.ElevatedButton(
                                    "Выбрать папку",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda _: (
                                        self.folder_picker.get_directory_path()
                                        if self.folder_picker
                                        else None
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=20,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=30,
                expand=True
            )

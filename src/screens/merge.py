import pathlib
from asyncio import sleep
from venv import logger

import flet as ft

from utils import API
from utils.install_pack import install_pack

from .screen import Screen


class MergeScreen(Screen):
    def __init__(self, navigator, api: API):
        self.navigator = navigator
        self.api = api

        # основная кнопка
        self.merge_button = ft.Button(
            "Совместить", height=60, width=300, on_click=self.merge_start
        )
        self.action_button = self.merge_button

        status_code, self.file_list = api.get_files(0, 100)
        self.keys_file = [pack["s3_key"] for pack in self.file_list]
        self.dropdown_options = []
        for pack in self.file_list:
            self.dropdown_options.append(
                ft.dropdown.DropdownOption(key=pack["s3_key"], text=pack["name"])
            )

        self.main_pack_menu = ft.Dropdown(
            options=self.dropdown_options,
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            enable_filter=True,
            editable=True,
            border_color=ft.Colors.WHITE,
            menu_height=self.navigator.page.height / 3,
        )

        self.second_pack_menu = ft.Dropdown(
            options=self.dropdown_options,
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            enable_filter=True,
            editable=True,
            border_color=ft.Colors.WHITE,
            menu_height=self.navigator.page.height / 3,
        )

        # контейнер, в который будем подставлять разные элементы (кнопка / прогресс / варианты)
        self.action_container = ft.Container(content=self.action_button)

        self.container: ft.Container = ft.Container(
            content=ft.Column(
                [
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Основной пак", size=20),
                                            ft.Container(
                                                self.main_pack_menu,
                                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Icon(name=ft.Icons.ADD_ROUNDED, size=50),
                                    ft.Column(
                                        [
                                            ft.Text("Доп. пак", size=20),
                                            ft.Container(
                                                self.second_pack_menu,
                                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.END,
                            ),
                            # вместо self.action_button теперь подставляем контейнер
                            self.action_container,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )

    def set_action_control(self, control: ft.Control) -> None:
        """Утилита для замены action-контрола (кнопка, прогресс, варианты и т.п.)."""
        self.action_button = control
        self.action_container.content = control
        self.navigator.page.update()

    def on_resize(self, e) -> None:
        pass

    def build(self) -> ft.Container:
        return self.container

    async def update_progress(self):
        timeout = 240
        self.result_key = ""
        while timeout > 0:
            timeout -= 1
            await sleep(1)
            status_code, resp_json = self.api.get_task_status(self.task_id)
            logger.info(resp_json)
            if resp_json.get("progress", "") == "Status.DONE":
                self.result_key = resp_json.get("result_key", "")
                break

        if self.result_key:
            self.show_result_actions()
        else:
            self.cancel_merge(None)

    def show_result_actions(self) -> None:
        """Показываем варианты: скачать и установить пак или отменить."""

        download_btn = ft.Button(
            "Скачать и установить пак",
            height=50,
            width=300,
            on_click=self.download_and_install,
        )
        cancel_btn = ft.Button(
            "Отменить",
            height=50,
            width=300,
            on_click=self.cancel_merge,
        )

        actions_column = ft.Column(
            [
                download_btn,
                cancel_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.set_action_control(actions_column)

    def download_and_install(self, e) -> None:
        """Заглушка: тут можно повесить логику скачивания/установки по self.result_key."""
        page = self.navigator.page

        if self.result_key:
            progress_bar = ft.ProgressRing(
                width=100,
                height=100,
                stroke_width=50,
                stroke_align=-1,
                stroke_cap=ft.StrokeCap.ROUND,
            )
            uuid = pathlib.Path(self.result_key).stem
            self.set_action_control(progress_bar)
            for progress in self.api.download_file(
                f"https://{self.result_key}", uuid, None
            ):
                progress_bar.value = progress / 100
                self.set_action_control(progress_bar)
                print(progress)
            install_pack(
                uuid,
                self.navigator.page.client_storage.get("lsslaucher.dota_path"),
                self.api,
            )
            page.update()
        self.cancel_merge(None)
        page.update()

    def cancel_merge(self, e) -> None:
        """Отмена: возвращаем исходную кнопку 'Совместить'."""
        self.set_action_control(self.merge_button)

    def merge_start(self, e) -> None:
        # в начало: заменяем action_button на крутящийся ProgressRing
        progress = ft.ProgressRing(width=40, height=40)
        self.set_action_control(progress)

        main_key = self.main_pack_menu.value
        second_key = self.second_pack_menu.value

        if main_key and second_key:
            _, self.task_id = self.api.merge_pack(main_key, second_key)
            self.task_id = self.task_id
            self.navigator.page.run_task(self.update_progress)
        else:
            # если не выбраны паки, возвращаем кнопку и показываем сообщение
            self.set_action_control(self.merge_button)
            self.navigator.page.snack_bar = ft.SnackBar(
                ft.Text("Выберите оба пака перед запуском объединения.")
            )
            self.navigator.page.snack_bar.open = True
            self.navigator.page.update()

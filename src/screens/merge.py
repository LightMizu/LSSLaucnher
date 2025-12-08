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
        self.merge_button = ft.FilledButton(
            "Начать совмещение",  # type: ignore
            height=60,
            width=300,
            on_click=self.merge_start,
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_SECONDARY,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=25, weight="bold")),
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
            border_radius=7,
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
                            ft.Container(expand=35),
                            ft.Row(
                                [
                                    ft.Container(
                                        ft.Column(
                                            [
                                                ft.Text("Основной пак", size=20),
                                                ft.Container(
                                                    self.main_pack_menu,
                                                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                                    border_radius=7,
                                                ),
                                            ],
                                        ),
                                        bgcolor=ft.Colors.ON_SECONDARY,
                                        border_radius=15,
                                        padding=ft.padding.symmetric(
                                            vertical=30, horizontal=15
                                        ),
                                    ),
                                    ft.Container(
                                        ft.Icon(name=ft.Icons.ADD_ROUNDED, size=50),
                                        border_radius=25,
                                        bgcolor=ft.Colors.ON_SECONDARY,
                                    ),
                                    ft.Container(
                                        ft.Column(
                                            [
                                                ft.Text("Доп. пак", size=20),
                                                ft.Container(
                                                    self.second_pack_menu,
                                                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                                    border_radius=7,
                                                ),
                                            ],
                                        ),
                                        bgcolor=ft.Colors.ON_SECONDARY,
                                        border_radius=15,
                                        padding=ft.padding.symmetric(
                                            vertical=30, horizontal=15
                                        ),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            # вместо self.action_button теперь подставляем контейнер
                            ft.Container(expand=1),
                            self.action_container,
                            ft.Text(
                                "Выберите Основной пак, затем дополнительный.\n Основной пак имеет приоритет.",
                                color=ft.Colors.OUTLINE_VARIANT,
                                size=18,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(expand=30),
                            ft.Text(
                                "Учтите что это бета-версия и совмещение может работать некорректно!",
                                color=ft.Colors.OUTLINE_VARIANT,
                                size=30,
                            ),
                        ],
                        expand=True,
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
            progress_bar = ft.ProgressBar(
                height=50, width=self.navigator.page.width / 2, border_radius=30
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

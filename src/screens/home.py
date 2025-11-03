import flet as ft

from utils.api import API
from utils.helpers import find_by_key, get_uuid_file, human_readable_size, open_folder
from utils.install_pack import (
    delete_pack,
    install_pack,
    launch_dota,
    patch_dota,
    APP_DATA_PATH,
)
from .screen import Screen
import os
from loguru import logger
from typing import List
from typing import Any, Callable, Iterable

class PackCard(ft.Container):
    def add_to_favorites(self, e):
        favorite = []
        logger.info(f"Switch favorites id:{self.id_file}")
        if e.page.client_storage.contains_key("lsslaucher.favorites"):
            favorite = e.page.client_storage.get("lsslaucher.favorites")
        logger.info(f"List favorites ids:{favorite}")
        if self.id_file in favorite:
            logger.info(f"Self id exists remove id:{self.id_file}")
            favorite.remove(self.id_file)
            e.control.icon = ft.Icons.STAR_BORDER_ROUNDED
        else:
            logger.info(f"Self id not exists adding id:{self.id_file}")
            favorite.append(self.id_file)
            e.control.icon = ft.Icons.STAR_ROUNDED
        e.page.client_storage.set("lsslaucher.favorites", favorite)
        logger.info(f"Updated favorites ids:{favorite}")
        e.page.update()

    def __init__(
        self, file: dict, select_button: ft.Control, favorites: List[int]
    ):
        self.select_button = select_button
        self.progress_ring = ft.ProgressRing(width=20, height=20, visible=False)
        self.id_file = file["id"]
        super().__init__(
            content=ft.SafeArea(
                ft.Row(
                    [
                        ft.Text(file["name"], expand=True),
                        ft.FilledButton(
                            "Скрины",
                            url=file["screenshost"],
                            bgcolor=ft.Colors.INVERSE_PRIMARY,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(
                                text_style=ft.TextStyle(weight=ft.FontWeight.W_700)
                            ),
                        ),
                        ft.Text(
                            human_readable_size(file["size"]),
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.SECONDARY,
                            width=100,
                        ),
                        ft.IconButton(
                            icon=(
                                ft.Icons.STAR_ROUNDED
                                if file["id"] in favorites
                                else ft.Icons.STAR_BORDER_ROUNDED
                            ),
                            on_click=self.add_to_favorites,
                        ),
                        self.select_button,
                        self.progress_ring,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=30,
                ),
                minimum_padding=ft.padding.all(20),
            ),
            height=85,
            bgcolor=ft.Colors.ON_SECONDARY,
            expand=True,
            border_radius=20,
        )



FAVORITES_KEY = "lsslaucher.favorites"


class PackList(ft.ListView):
    """
    Отображает список паков с кнопками выбора.
    - files: итерируемый набор словарей с ключом "id"
    - on_select: коллбек вида (pack_id: str, button: ft.IconButton) -> None
    - page: экземпляр ft.Page (нужен для client_storage)
    """

    def __init__(
        self,
        files: Iterable[dict[str, Any]],
        on_select: Callable[[str, ft.IconButton], None],
        page: ft.Page,
    ) -> None:
        self.page: ft.Page = page
        self.on_select = on_select
        self.files: list[dict[str, Any]] = list(files)

        logger.info("Init PackList")

        # Кэшируем избранное и предрасчитываем позиции для сортировки
        self._favorite_ids: list[str] = self._read_favorites()
        self._fav_positions: dict[str, int] = {
            pack_id: idx for idx, pack_id in enumerate(self._favorite_ids)
        }

        # Строим контролы один раз
        controls = self._build_controls()

        super().__init__(
            controls=controls,
            height=float("inf"),
            spacing=10,
            # scroll=ft.ScrollMode.ADAPTIVE,  # включите при необходимости
        )

    # ---------- Публичные методы ----------

    def before_update(self) -> None:
        """
        Вызывается фреймворком перед прорисовкой: перечитываем избранное,
        пересортировываем и перестраиваем контролы без дублирования кода.
        """
        self._favorite_ids = self._read_favorites()
        self._fav_positions = {
            pack_id: idx for idx, pack_id in enumerate(self._favorite_ids)
        }

        logger.info("Updating PackList")
        logger.debug(f"Favorites: {self._favorite_ids}")

        self.controls = self._build_controls()
        super().before_update()

    # ---------- Внутренние вспомогательные ----------

    def _read_favorites(self) -> list[str]:
        """Безопасно читаем список избранного из client_storage."""
        if self.page.client_storage.contains_key(FAVORITES_KEY):
            fav = self.page.client_storage.get(FAVORITES_KEY)
            if isinstance(fav, list) and all(isinstance(x, int) for x in fav):
                return fav
            logger.warning(f"Favorites value has unexpected type: {fav}")
        return []

    def _ordered_files(self) -> list[dict[str, Any]]:
        """
        Возвращает файлы, отсортированные так, чтобы избранные были первыми,
        сохраняя их порядок из избранного.
        """
        def sort_key(item: dict[str, Any]) -> tuple[int, str]:
            pack_id = int(item.get("id", ""))
            # сначала по позиции в favorites (или бесконечность),
            # затем по id — стабильная сортировка для остальных
            pos = self._fav_positions.get(pack_id, float("inf"))
            return (pos, pack_id)

        return sorted(self.files, key=sort_key)

    def _make_select_button(
        self, pack_id: str
    ) -> ft.IconButton:
        """Создаёт кнопку выбора и вешает обработчик."""
        btn = ft.IconButton(ft.Icons.CIRCLE_OUTLINED)

        def _on_click(_):
            self.on_select(pack_id, btn)

        btn.on_click = _on_click
        return btn

    def _build_controls(self) -> list[ft.Control]:
        """Строит и возвращает список контролов для ListView."""
        ordered = self._ordered_files()
        logger.debug(f"Ordered {len(ordered)} files", )

        cards: list[ft.Control] = []
        for file in ordered:
            pack_id = int(file.get("id", ""))
            select_button = self._make_select_button(pack_id)
            # PackCard предполагается внешним классом
            card = PackCard(file, select_button, self._favorite_ids)
            cards.append(ft.Container(card, padding=ft.padding.only(right=15)))
        return cards

class HomeScreen(Screen):
    def update_files(self):
        
        self.packs_column = ft.SafeArea(
            ft.Stack(
                [
                    PackList(self.files, self.select_pack, self.navigator.page),
                    ft.Container(self.install_custom_pack_button, height=30, width=100),
                ],
                alignment=ft.alignment.bottom_left,
                expand=True,
            ),
            expand=True,
        )
        self.main_container = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.OutlinedButton(
                                text="Запустить игру",
                                height=70,
                                width=300,
                                on_click=self.launch,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight=ft.FontWeight.W_700)
                                ),
                            ),
                            ft.OutlinedButton(
                                text="Установить",
                                height=70,
                                width=300,
                                on_click=self.install_pack_handler,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight=ft.FontWeight.W_700)
                                ),
                            ),
                            ft.OutlinedButton(
                                text="Пофиксить VAC",
                                height=70,
                                width=300,
                                on_click=self.fix_vac,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight=ft.FontWeight.W_700)
                                ),
                            ),
                            ft.OutlinedButton(
                                text="Удалить",
                                height=70,
                                width=300,
                                on_click=self.delete_pack,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight=ft.FontWeight.W_700)
                                ),
                            ),
                            ft.Container(
                                ft.Image("icon.png", expand=True),
                                width=180,
                                height=180,
                                padding=ft.padding.all(10),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=500,
                    ),
                    ft.VerticalDivider(width=5, color=ft.Colors.PRIMARY),
                    self.packs_column,
                ],
                expand=True,
            ),
            alignment=ft.alignment.center,
        )
        self.navigator.page.update()

    def __init__(self, navigator, api: API):
        self.navigator = navigator
        self.api: API = api
        self.selected_pack = -1
        status_code, self.files = api.get_files(0, 100)
        self.list_files = []
        self.install_custom_pack_button = ft.Button(
            "+Свой пак",
            expand=True,
            on_click=lambda x: self.navigator.page.open(
                self.install_custom_pack_dialog
            ),
        )
        logger.info(f"APP_DATA_PATH: {APP_DATA_PATH}")
        self.install_custom_pack_dialog = ft.AlertDialog(
            modal=True,
            title="Установка своего пака",
            content=ft.Text(
                "Для установки пака нужно переместить vpk в папку лаунчера"
            ),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=lambda x: self.navigator.page.close(
                        self.install_custom_pack_dialog
                    ),
                ),
                ft.TextButton(
                    "Открыть папку", on_click=lambda x: open_folder(APP_DATA_PATH)
                ),
                ft.TextButton(
                    "Выбрать vpk",
                    on_click=self.get_custom_vpk,
                ),
            ],
        )
        self.custom_vpk_list = ft.RadioGroup(
            content=ft.Column(
                controls=[],
                height=self.navigator.page.height / 4,
                scroll=ft.ScrollMode.ADAPTIVE,
            )
        )
        self.select_custom_pack_dialog = ft.AlertDialog(
            modal=True,
            title="Выбор своего пака",
            content=self.custom_vpk_list,
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=lambda x: self.navigator.page.close(
                        self.select_custom_pack_dialog
                    ),
                ),
                ft.TextButton("Установить", on_click=self.install_custom),
            ],
        )

        self.update_files()

        self.status_text = ft.Text(size=30)
        self.error_text = ft.Text(size=25)
        self.status_icon = ft.Icon(size=50)
        self.status_dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    self.status_icon,
                    self.status_text,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            content=self.error_text,
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(20),
            content_padding=ft.padding.all(50),
            on_dismiss=self.on_dismiss,
        )

        logger.info("HomeScreen initialized with packs loaded")

    def build(self) -> ft.Container:
        self.update_files()
        return self.main_container

    def get_custom_vpk(self, e):
        assert isinstance(self.custom_vpk_list.content, ft.Column)
        files = [
            f
            for f in os.listdir(APP_DATA_PATH)
            if os.path.isfile(os.path.join(APP_DATA_PATH, f))
        ]
        files.sort()
        list_files = [
            ft.Radio(value=x, label=os.path.splitext(x)[0])
            for x in files
            if os.path.splitext(x)[1].lower() == ".vpk"
        ]
        self.custom_vpk_list.content.controls = list_files
        self.navigator.page.close(self.install_custom_pack_dialog)
        self.navigator.page.open(self.select_custom_pack_dialog)
        logger.info(f"Custom VPKs listed: {[f.value for f in list_files]}")

    def on_resize(self, e):
        self.packs_column.width = self.navigator.page.width - 335
        self.navigator.page.update()
        logger.debug(
            f"HomeScreen resized: width={self.navigator.page.width} height={self.navigator.page.height}"
        )

    def select_pack(self, id_pack: int, button: ft.IconButton):
        card = next(c for c in self.list_files if c.select_button == button)
        card.progress_ring.value = None
        card.progress_ring.visible = True
        card.select_button.visible = False
        self.navigator.page.update()

        file = find_by_key(self.files, "id", id_pack)
        assert file
        name_file = get_uuid_file(file["id"])
        logger.info(f"Downloading pack {file['name']} ({name_file})")

        for progress in self.api.download_file(
            file["download_url"], name_file, file["md5"]
        ):
            card.progress_ring.value = progress / 100
            self.navigator.page.update()

        card.progress_ring.visible = False
        card.select_button.visible = True

        for i, card in enumerate(self.list_files):
            card.select_button.icon = ft.Icons.CIRCLE_OUTLINED
        button.icon = ft.Icons.CIRCLE_ROUNDED

        self.selected_pack = id_pack
        self.navigator.page.update()
        logger.success(f"Pack {file['name']} selected and downloaded")

    def on_dismiss(self, e):
        self.status_dialog.content = self.error_text
        self.status_dialog.title_padding = ft.padding.all(20)

    def open_status_dialog(self, status, text, icon):
        if not text:
            self.status_dialog.content = None
            self.status_dialog.title_padding = ft.padding.only(25, 21, 25, 0)
        self.status_icon.name = icon
        self.status_text.value = status
        self.error_text.value = text
        self.navigator.page.open(self.status_dialog)
        logger.info(f"Status dialog: {status}")

    def launch(self, e):
        launch_dota()
        logger.info("Launched Dota 2")

    def delete_pack(self, _):
        self.navigator.page.update()
        path = self.navigator.page.client_storage.get("lsslaucher.dota_path")
        if path == "":
            self.open_status_dialog(
                "Ошибка: Не установлен путь до папки дота 2",
                None,
                ft.Icons.CLOSE_ROUNDED,
            )
            return
        delete_pack(path)
        self.open_status_dialog("Успех", "Пак удалён", ft.Icons.CHECK_ROUNDED)
        logger.success("Deleted pack")
        self.navigator.page.update()

    def install_pack_handler(self, _):
        self.navigator.page.update()
        id_pack = self.selected_pack
        path = self.navigator.page.client_storage.get("lsslaucher.dota_path")
        if path == "":
            self.open_status_dialog(
                "Ошибка: Не установлен путь до папки дота 2",
                None,
                ft.Icons.CLOSE_ROUNDED,
            )
            return
        if id_pack == -1:
            self.open_status_dialog(
                "Ошибка: Пак не выбран", None, ft.Icons.CLOSE_ROUNDED
            )
            return

        name_file = get_uuid_file(id_pack)
        logger.info(f"Installing pack {name_file}")
        install_pack(name_file, path, self.api)
        self.open_status_dialog(
            "Успех", "Пак установлен, запустите игру", ft.Icons.CHECK_ROUNDED
        )
        self.navigator.page.update()

    def fix_vac(self, e):
        path = self.navigator.page.client_storage.get("lsslaucher.dota_path")
        if path == "":
            self.open_status_dialog(
                "Ошибка: Не установлен путь до папки дота 2",
                None,
                ft.Icons.CLOSE_ROUNDED,
            )
            return
        patch_dota(path)
        self.open_status_dialog(
            "Успех", "Ошибка VAC исправлена", ft.Icons.CHECK_ROUNDED
        )
        logger.success("VAC fixed")

    def install_custom(self, e):
        if not self.custom_vpk_list.value:
            return
        self.navigator.page.close(self.install_custom_pack_dialog)
        filename = self.custom_vpk_list.value
        path = self.navigator.page.client_storage.get("lsslaucher.dota_path")
        if path == "":
            self.open_status_dialog(
                "Ошибка: Не установлен путь до папки дота 2",
                None,
                ft.Icons.CLOSE_ROUNDED,
            )
            return
        install_pack(filename, path, self.api)
        self.open_status_dialog(
            "Успех", "Пак установлен, запустите игру", ft.Icons.CHECK_ROUNDED
        )
        logger.success(f"Custom pack {filename} installed")
        self.navigator.page.update()

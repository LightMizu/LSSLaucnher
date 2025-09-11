import flet as ft

from screens import HomeScreen, SettingsScreen, AboutScreen, AuthScreen
from utils import API, AuthUtil, ScreenManager, get_dota2_install_path
from pathlib import Path

def nav_segment(value: str, label: str, disabled: bool = False):
    return ft.Segment(
        value=value,
        disabled=disabled,
        label=ft.Container(
            content=ft.Text(
                label,
                text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.BOLD,
                size=20,
            ),
            alignment=ft.alignment.center,
            height=70,
        ),
    )


class Launcher:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "LSSLauncher"
        self.page.window.icon = str(Path('src/assets/icon.ico'))
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1200
        self.page.window.height = 730
        self.page.window.focused = True
        self.page.window.title_bar_hidden = False
        self.page.window.resizable = False
        self.page.window.maximizable = False
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.screen_manager = ScreenManager(page)
        self.api = API()
        self.auth_util = AuthUtil(self.api)
        self.set_default_path()

    def set_default_path(self):
        path = self.page.client_storage.get("lsslaucher.dota_path")
        if not path:
            self.page.client_storage.set(
                "lsslaucher.dota_path", get_dota2_install_path() or ""
            )

    def try_authenticate_user(self):
        token = self.page.client_storage.get("lsslaucher.token")
        if not token:
            self.show_auth_screen()
        else:
            self.api.token = token
            if self.auth_util.check_token_is_valid():
                self.run_laucher()
            else:
                self.show_auth_screen()

    def show_auth_screen(self):
        self.screen_manager.navigate_to("auth")
        self.page.add(self.screen_manager.get_main_container())

    def handle_change(self, e: ft.ControlEvent):
        assert e.data
        assert self.page.width

        value = e.data[2:-2]
        page_width = self.page.width 
        segment_width = page_width/4
        self.selector_container.padding=ft.padding.only(right=segment_width*(3-self.pages.index(value)),left=segment_width*self.pages.index(value))
        
        self.page.update()
        self.screen_manager.navigate_to(value)

    def setup_appbar(self):
        assert self.page.window.width
        #self.page.show_semantics_debugger = True
        self.page.update()
        page_width = self.page.window.width
        self.selector = ft.Container(
            height=2,
            bgcolor=ft.Colors.PRIMARY,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_IN),
            expand=True,
            expand_loose=True)
        self.pages_container: ft.Container = ft.Container(
            content=ft.Row(
                [
                    ft.SegmentedButton(
                        on_change=self.handle_change,
                        allow_multiple_selection=False,
                        selected_icon=ft.Icon(size=0),
                        selected={"home"},  # выбран по умолчанию
                        segments=[
                            nav_segment("home", "Главная"),
                            nav_segment("settings", "Настройки"),
                            nav_segment("shop", "Магазин", disabled=True),
                            nav_segment("about", "О нас"),
                        ],
                        height=70,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=0),
                            alignment=ft.alignment.center,
                        ),
                        expand=True,
                    )
                ]
            ),
            expand=True,
            width=float('inf'),
            height=70,
        )
        self.pages = ["home", "settings", "shop", "about"]
        segment_width = page_width//4

        self.selector_container = ft.Container(self.selector, expand=True,padding=ft.padding.only(right=segment_width*3),animate=ft.Animation(250, ft.AnimationCurve.EASE_IN))
        self.app_bar = ft.Column(
            [
                self.pages_container,
                self.selector_container
            ]
        )

        #self.selector.width = (1250) / 4  # type: ignore
        #self.page.appbar = self.app_bar  # type: ignore

    def setup_auth_screen(self):
        self.screen_manager.add_screen(
            "auth",
            AuthScreen(self.screen_manager, self.api, self.try_authenticate_user),
        )

    def move_window(self, e):
        self.page.window.start_dragging()
        

    def setup_screens(self):
        # Initialize screens with navigator dependency
        self.screen_manager.add_screen(
            "home", HomeScreen(self.screen_manager, self.api)
        )
        self.screen_manager.add_screen("settings", SettingsScreen(self.screen_manager))
        self.screen_manager.add_screen("about", AboutScreen(self.screen_manager))

    def run_laucher(self):
        self.setup_screens()
        self.setup_appbar()
        self.page.window.frameless = True
        self.page.clean()
        self.screen_manager.navigate_to("home")
        self.move_bar = ft.GestureDetector(
            content=ft.Container(
                ft.Stack(
                    [
                        ft.Text("Заголовок окна"),
                        ft.Container(
                            ft.IconButton(ft.Icons.CLOSE_ROUNDED,icon_size=15, width=30,height=30),
                            alignment=ft.alignment.top_right,
                        ),
                    ],
                    alignment=ft.alignment.center,
                    height=30,
                    width=self.page.width,
                ),
                bgcolor=ft.Colors.ON_SECONDARY,
                border_radius=ft.border_radius.vertical(15),
            ),
            on_vertical_drag_update=self.move_window,
        )
        self.page.padding=0
        self.page.bgcolor = ft.Colors.TRANSPARENT
        self.page.add(
                ft.Column([self.move_bar,self.app_bar, self.screen_manager.get_main_container()],expand=True,spacing=0)
        )

    def run(self):
        self.setup_auth_screen()
        self.try_authenticate_user()

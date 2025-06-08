import flet as ft
from src.launcher.screens import HomeScreen, SettingsScreen, AboutScreen
from src.launcher.utils import ScreenManager


class Laucher:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "LSSLaucnher"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1000
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.screen_manager = ScreenManager(page)

    def setup_appbar(self):
        self.page.appbar = ft.AppBar(
            title=ft.Row(
                    [
                        ft.Button("Главная"),
                        ft.Button("Настройки"),
                        ft.Button("Мор скины"),
                        ft.Button("О нас"),
                    ],
                    
                ),
            bgcolor=ft.Colors.PURPLE_200,
        )

    def setup_screens(self):
        # Initialize screens with navigator dependency
        self.screen_manager.add_screen("home", HomeScreen(self.screen_manager))
        self.screen_manager.add_screen("settings", SettingsScreen(self.screen_manager))
        self.screen_manager.add_screen("profile", AboutScreen(self.screen_manager))

    def run(self):
        self.setup_screens()
        self.setup_appbar()
        self.page.add(self.screen_manager.get_main_container())
        self.screen_manager.navigate_to("home")

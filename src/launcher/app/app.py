import flet as ft

from src.launcher.screens import HomeScreen, SettingsScreen, AboutScreen, AuthScreen
from src.launcher.utils import API, AuthUtil, ScreenManager, get_dota2_install_path

class Laucher:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = 'LSSLaucnher'
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1000
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_300)
        self.screen_manager = ScreenManager(page)
        self.api = API()
        self.auth_util = AuthUtil(self.api)
        self.set_default_path()

    def set_default_path(self):
        path = self.page.client_storage.get('lsslaucher.dota_path')
        if not path:
            self.page.client_storage.set('lsslaucher.dota_path',get_dota2_install_path())

    def try_authenticate_user(self):
        token = self.page.client_storage.get('lsslaucher.token')
        if not token:
            self.show_auth_screen()
        else:
            self.api.token = token
            if self.auth_util.check_token_is_valid():
                self.run_laucher()
            else:
                self.show_auth_screen()

    def show_auth_screen(self):
        self.screen_manager.navigate_to('auth')
        self.page.add(self.screen_manager.get_main_container())

    def setup_appbar(self):
        self.page.appbar = ft.AppBar(
            title=ft.Row(
                    [
                        
                        ft.Button('Главная'),
                        ft.Button('Настройки'),
                        ft.Button('Магазин'),
                        ft.Button('О нас'),
                    ],
                    
                ),
            bgcolor=ft.Colors.PURPLE_200,
        )

    def setup_auth_screen(self):
        self.screen_manager.add_screen('auth', AuthScreen(self.screen_manager, self.api, self.try_authenticate_user))

    def setup_screens(self):
        # Initialize screens with navigator dependency        
        self.screen_manager.add_screen('home', HomeScreen(self.screen_manager, self.api))
        self.screen_manager.add_screen('settings', SettingsScreen(self.screen_manager))
        self.screen_manager.add_screen('profile', AboutScreen(self.screen_manager))

    def run_laucher(self):
        self.setup_screens()
        self.setup_appbar()
        self.page.clean()
        self.screen_manager.navigate_to('home')
        self.page.add(self.screen_manager.get_main_container())

    def run(self):
        self.setup_auth_screen()
        self.try_authenticate_user()
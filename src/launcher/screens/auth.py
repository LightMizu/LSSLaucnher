from .screen import Screen
import flet as ft
from src.launcher.utils import API, get_hwid


class AuthScreen(Screen):
    def __init__(self, navigator, api: API, on_succes_auth):
        self.navigator = navigator
        self.api: API = api
        self.on_succes_auth = on_succes_auth

    def on_resize(self, e) -> None:
        self.auth_container.height = self.navigator.page.height
        self.auth_container.width = self.navigator.page.width
        self.login_field.width = self.navigator.page.width // 4
        self.password_field.width = self.navigator.page.width // 4
        self.navigator.page.update()

    def auth(self, e):

        if (
            self.api.get_token(
                self.login_field.value, self.password_field.value, get_hwid() #type: ignore
            )
            == 200
        ):
            self.navigator.page.client_storage.set('lsslaucher.token', self.api.token)
            self.on_succes_auth()
        else:
            self.login_field.border_color = ft.Colors.RED
            self.password_field.border_color = ft.Colors.RED
            self.login_field.value = ''
            self.password_field.value = ''
            self.error_text.value = 'Неверный логин или пароль'
            self.navigator.page.update()

    def build(self) -> ft.Container:
        self.login_field: ft.TextField = ft.TextField(
            hint_text='Login', width=self.navigator.page.width // 4
        )
        self.password_field: ft.TextField = ft.TextField(
            hint_text='Password', width=self.navigator.page.width // 4
        )
        self.error_text = ft.Text()
        self.auth_container = ft.Container(
            content=ft.Column(
                [
                    self.login_field,
                    self.password_field,
                    self.error_text,
                    ft.ElevatedButton('Login', on_click=self.auth),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=self.navigator.page.height,
            width=self.navigator.page.width,
        )
        return self.auth_container

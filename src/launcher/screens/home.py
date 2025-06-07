import flet as ft
from .screen import Screen

# Interface for screens (ISP, DIP)


# Concrete screen implementations (SRP, LSP)
class HomeScreen(Screen):
    def __init__(self, navigator):
        self.navigator = navigator

    def build(self) -> ft.Container:
        self.navigator.page.on_resized = self.resize
        self.packs_column = ft.SafeArea(ft.Column(
            [
                ft.Container(
                    content=ft.SafeArea(
                        ft.Row(
                            [
                                ft.Text("Пак на всех из оффициальных"),
                                ft.FilledButton("Скрины"),
                                ft.Icon(ft.Icons.CIRCLE_OUTLINED),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    minimum_padding=20,
                    ),
                    height=75,
                        bgcolor=ft.Colors.ON_SECONDARY,
                        border_radius=20,
                )
            ]
            * 100,
            width=self.navigator.page.width - 535,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),minimum_padding=20)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.OutlinedButton(text="Установить", height=50, width=200),
                            ft.OutlinedButton(
                                text="Пофиксить VAC", height=50, width=200
                            ),
                            ft.OutlinedButton(text="Удалить", height=50, width=200),
                            ft.Image("assets/logo.png", height=200, width=200),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=500,
                    ),
                    ft.VerticalDivider(width=5, color=ft.Colors.PRIMARY),
                    self.packs_column,
                ]
            ),
            alignment=ft.alignment.center,
        )

    def resize(self, e):
        self.packs_column.width = self.navigator.page.width - 535
        self.navigator.page.update()

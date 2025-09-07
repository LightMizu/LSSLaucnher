from abc import ABC, abstractmethod
import flet as ft

class Screen(ABC):
    @abstractmethod
    def on_resize(self, e) -> None:
        pass

    @abstractmethod
    def build(self) -> ft.Container:
        pass
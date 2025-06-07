from abc import ABC, abstractmethod
import flet as ft

class Screen(ABC):
    @abstractmethod
    def build(self) -> ft.Container:
        pass
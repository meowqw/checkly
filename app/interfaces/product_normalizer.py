"""Интерфейс нормализации товаров."""
from abc import ABC, abstractmethod

from app.dto.receipts import ProductNormalizerInputDTO, ProductNormalizerOutputDTO


class ProductNormalizerInterface(ABC):
    @abstractmethod
    def normalize_items(self, dto: ProductNormalizerInputDTO) -> ProductNormalizerOutputDTO:
        """Нормализовать неизвестные товары и определить категории."""

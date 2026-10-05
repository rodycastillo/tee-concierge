from dataclasses import dataclass
from decimal import Decimal

SIZE_ORDER = ("XS", "S", "M", "L", "XL", "XXL")
LOW_STOCK_THRESHOLD = 3


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    category_id: int
    name: str
    description: str
    material: str
    price: Decimal  # PEN
    image_url: str | None = None
    active: bool = True


@dataclass(frozen=True, slots=True)
class Variant:
    """A purchasable SKU: one product in one size and color."""

    id: int
    product_id: int
    sku: str
    size: str
    color: str
    stock: int

    @property
    def available(self) -> bool:
        return self.stock > 0


def format_price(amount: Decimal) -> str:
    """Peruvian soles: Decimal('59.9') -> 'S/ 59.90'. Never floats for money."""
    return f"S/ {amount:,.2f}"


def size_sort_key(size: str) -> tuple[int, str]:
    return (SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER), size)

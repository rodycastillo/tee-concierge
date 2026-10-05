"""Validated catalog and FAQ management for the store owner.

Limits exist because everything saved here ends up inside a WhatsApp message, which
rejects bodies over 1024 characters. Rejecting long text on save is better than a
customer hitting a broken screen later.
"""

from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlparse

from tee_concierge.domain.catalog import SIZE_ORDER, Category, Product, Variant
from tee_concierge.domain.errors import InvalidInputError
from tee_concierge.domain.ports import AdminCatalogRepository

FAQ_TOPICS = ("sizes", "shipping", "payment", "returns")
MAX_FAQ_CHARS = 1000
MAX_DESCRIPTION_CHARS = 700
MAX_NAME_CHARS = 120
MAX_PRICE = Decimal("100000")


def _text(value: str, field: str, limit: int, *, required: bool = True) -> str:
    value = value.strip()
    if required and not value:
        raise InvalidInputError(f"{field} must not be empty")
    if len(value) > limit:
        raise InvalidInputError(f"{field} must be at most {limit} characters")
    return value


def _price(value: Decimal | str | float) -> Decimal:
    try:
        price = Decimal(str(value))
    except InvalidOperation as exc:
        raise InvalidInputError("price is not a number") from exc
    if not price.is_finite() or price <= 0 or price > MAX_PRICE:
        raise InvalidInputError(f"price must be between 0 and {MAX_PRICE}")
    return price.quantize(Decimal("0.01"))


def _image(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or len(url) > 500:
        raise InvalidInputError("image_url must be an https URL (WhatsApp requires it)")
    return url


def _stock(value: int) -> int:
    if value < 0:
        raise InvalidInputError("stock must not be negative")
    return value


class CatalogAdmin:
    def __init__(self, repo: AdminCatalogRepository) -> None:
        self._repo = repo

    async def create_category(self, name: str) -> Category:
        return await self._repo.create_category(_text(name, "name", 80))

    async def list_products(self, offset: int = 0, limit: int = 50) -> list[Product]:
        return await self._repo.list_all_products(offset, limit)

    async def create_product(
        self,
        category_id: int,
        name: str,
        price: Decimal | str | float,
        description: str = "",
        material: str = "",
        image_url: str | None = None,
    ) -> Product:
        return await self._repo.create_product(
            category_id,
            _text(name, "name", MAX_NAME_CHARS),
            _text(description, "description", MAX_DESCRIPTION_CHARS, required=False),
            _text(material, "material", MAX_NAME_CHARS, required=False),
            _price(price),
            _image(image_url),
        )

    async def update_product(self, product_id: int, changes: dict[str, Any]) -> Product:
        clean: dict[str, Any] = {}
        for key, value in changes.items():
            if key == "name":
                clean[key] = _text(value, "name", MAX_NAME_CHARS)
            elif key == "description":
                clean[key] = _text(value, "description", MAX_DESCRIPTION_CHARS, required=False)
            elif key == "material":
                clean[key] = _text(value, "material", MAX_NAME_CHARS, required=False)
            elif key == "price":
                clean[key] = _price(value)
            elif key == "image_url":
                clean[key] = _image(value)
            elif key in ("active", "category_id"):
                clean[key] = value
            else:
                raise InvalidInputError(f"field {key!r} cannot be changed")
        return await self._repo.update_product(product_id, clean)

    async def create_variant(
        self, product_id: int, sku: str, size: str, color: str, stock: int
    ) -> Variant:
        size = size.strip().upper()
        if size not in SIZE_ORDER:
            raise InvalidInputError(f"size must be one of {', '.join(SIZE_ORDER)}")
        return await self._repo.create_variant(
            product_id,
            _text(sku, "sku", 64),
            size,
            _text(color, "color", 40),
            _stock(stock),
        )

    async def set_stock(self, variant_id: int, stock: int) -> Variant:
        return await self._repo.set_stock(variant_id, _stock(stock))

    async def set_faq(self, topic: str, body: str) -> None:
        if topic not in FAQ_TOPICS:
            raise InvalidInputError(f"topic must be one of {', '.join(FAQ_TOPICS)}")
        await self._repo.set_faq(topic, _text(body, "body", MAX_FAQ_CHARS))

    async def list_faq(self) -> dict[str, str]:
        return await self._repo.list_faq()

from decimal import Decimal
from typing import Any

import pytest

from tee_concierge.application.admin import CatalogAdmin
from tee_concierge.domain.errors import InvalidInputError


class Capture:
    """Records what reaches the repository, so validation is tested in isolation."""

    def __getattr__(self, name: str) -> Any:
        async def call(*args: Any, **kwargs: Any) -> Any:
            self.last = (name, args, kwargs)

        return call


@pytest.fixture
def admin() -> CatalogAdmin:
    return CatalogAdmin(Capture())


@pytest.mark.parametrize("price", ["0", "-5", "abc", "nan", "inf", "1000000"])
async def test_invalid_prices_are_rejected(admin: CatalogAdmin, price: str) -> None:
    with pytest.raises(InvalidInputError):
        await admin.create_product(1, "Polo", price)


async def test_price_is_normalized_to_cents() -> None:
    repo = Capture()
    await CatalogAdmin(repo).create_product(1, " Polo ", "59.9")
    _, args, _ = repo.last
    assert args[1] == "Polo" and args[4] == Decimal("59.90")


@pytest.mark.parametrize(
    "url", ["http://x.com/a.jpg", "javascript:alert(1)", "ftp://x/a", "https://"]
)
async def test_only_https_image_urls_are_accepted(admin: CatalogAdmin, url: str) -> None:
    with pytest.raises(InvalidInputError):
        await admin.create_product(1, "Polo", "10", image_url=url)


async def test_text_that_would_break_a_whatsapp_message_is_rejected(admin: CatalogAdmin) -> None:
    with pytest.raises(InvalidInputError):
        await admin.create_product(1, "Polo", "10", description="x" * 701)
    with pytest.raises(InvalidInputError):
        await admin.set_faq("shipping", "x" * 1001)
    with pytest.raises(InvalidInputError):
        await admin.create_product(1, "   ", "10")


async def test_stock_size_and_faq_topic_are_validated(admin: CatalogAdmin) -> None:
    with pytest.raises(InvalidInputError):
        await admin.set_stock(1, -1)
    with pytest.raises(InvalidInputError):
        await admin.create_variant(1, "SKU", "XXXL", "Negro", 1)
    with pytest.raises(InvalidInputError):
        await admin.set_faq("secrets", "hola")


async def test_only_whitelisted_product_fields_can_change(admin: CatalogAdmin) -> None:
    with pytest.raises(InvalidInputError):
        await admin.update_product(1, {"id": 99})

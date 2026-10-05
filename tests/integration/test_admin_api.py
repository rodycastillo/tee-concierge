"""The admin API against real SQL repositories (SQLite), through the HTTP layer."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from tee_concierge.application.admin import CatalogAdmin
from tee_concierge.config import Settings, get_settings
from tee_concierge.infrastructure.persistence.admin_repository import (
    SqlAdminCatalogRepository,
    SqlUsageRepository,
)
from tee_concierge.infrastructure.persistence.catalog_repository import SqlCatalogRepository
from tee_concierge.infrastructure.persistence.database import create_sessionmaker
from tee_concierge.infrastructure.persistence.models import Base
from tee_concierge.infrastructure.persistence.repository import SqlMessageRepository
from tee_concierge.interfaces.api.main import create_app

KEY = {"X-Admin-Key": "k3y"}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/admin.db")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sessions = create_sessionmaker(engine)
        app.state.repo = SqlMessageRepository(sessions)
        app.state.catalog = SqlCatalogRepository(sessions)
        app.state.usage = SqlUsageRepository(sessions)
        app.state.catalog_admin = CatalogAdmin(SqlAdminCatalogRepository(sessions))
        yield
        await engine.dispose()

    app = create_app(lifespan=lifespan)
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, admin_api_key="k3y")
    with TestClient(app) as test_client:
        yield test_client


def test_admin_requires_the_key(client: TestClient) -> None:
    assert client.get("/admin/categories").status_code == 401
    assert client.get("/admin/categories", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/admin/categories", headers=KEY).status_code == 200


def test_admin_is_hidden_when_no_key_is_configured(tmp_path: Path) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    assert TestClient(app).get("/admin/stats", headers=KEY).status_code == 404


def test_owner_manages_the_catalog_and_the_bot_sees_it(client: TestClient) -> None:
    category = client.post("/admin/categories", json={"name": "Nuevos"}, headers=KEY)
    assert category.status_code == 201
    assert client.post("/admin/categories", json={"name": "Nuevos"}, headers=KEY).status_code == 409

    product = client.post(
        "/admin/products",
        json={"category_id": category.json()["id"], "name": "Polo Sol", "price": "49.9"},
        headers=KEY,
    ).json()
    assert product["price"] == "49.90" and product["active"] is True

    variant = client.post(
        f"/admin/products/{product['id']}/variants",
        json={"sku": "SOL-M-AMA", "size": "m", "color": "Amarillo", "stock": 5},
        headers=KEY,
    )
    assert variant.status_code == 201 and variant.json()["size"] == "M"
    dup = client.post(
        f"/admin/products/{product['id']}/variants",
        json={"sku": "SOL-M-AMA", "size": "L", "color": "Amarillo", "stock": 1},
        headers=KEY,
    )
    assert dup.status_code == 409

    restock = client.patch(
        f"/admin/variants/{variant.json()['id']}", json={"stock": 0}, headers=KEY
    )
    assert restock.json()["stock"] == 0

    hidden = client.patch(f"/admin/products/{product['id']}", json={"active": False}, headers=KEY)
    assert hidden.json()["active"] is False
    assert [p["name"] for p in client.get("/admin/products", headers=KEY).json()] == ["Polo Sol"]


def test_validation_errors_are_422_and_unknown_ids_404(client: TestClient) -> None:
    assert client.patch("/admin/variants/999", json={"stock": 1}, headers=KEY).status_code == 404
    assert (
        client.post(
            "/admin/products", json={"category_id": 1, "name": "x", "price": "1"}, headers=KEY
        ).status_code
        == 404
    )
    cat = client.post("/admin/categories", json={"name": "C"}, headers=KEY).json()["id"]
    bad = client.post(
        "/admin/products", json={"category_id": cat, "name": "x", "price": "-1"}, headers=KEY
    )
    assert bad.status_code == 422


def test_faq_is_editable_and_listed(client: TestClient) -> None:
    assert (
        client.put("/admin/faq/shipping", json={"body": "Envío gratis"}, headers=KEY).status_code
        == 200
    )
    assert client.get("/admin/faq", headers=KEY).json() == {"shipping": "Envío gratis"}
    assert client.put("/admin/faq/unknown", json={"body": "x"}, headers=KEY).status_code == 422


def test_stats_and_history_endpoints(client: TestClient) -> None:
    assert client.get("/admin/conversations/51911111111/messages", headers=KEY).json() == []
    stats = client.get("/admin/stats", headers=KEY).json()
    assert stats == {
        "inbound_messages": 0,
        "outbound_messages": 0,
        "customers": 0,
        "top_menu_nodes": [],
    }


def test_metrics_endpoint_is_exposed(client: TestClient) -> None:
    body = client.get("/metrics/").text
    assert "tee_webhook_requests_total" in body

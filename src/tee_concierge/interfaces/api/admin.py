import hmac
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from tee_concierge.application.admin import CatalogAdmin
from tee_concierge.config import Settings, get_settings
from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.ports import CatalogRepository, MessageRepository, UsageRepository


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_key: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.admin_api_key.get_secret_value()
    if not expected:
        raise HTTPException(status_code=404)  # admin API disabled: pretend it does not exist
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="invalid admin key")


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _admin(request: Request) -> CatalogAdmin:
    admin: CatalogAdmin = request.app.state.catalog_admin
    return admin


def _catalog(request: Request) -> CatalogRepository:
    catalog: CatalogRepository = request.app.state.catalog
    return catalog


def _messages(request: Request) -> MessageRepository:
    repo: MessageRepository = request.app.state.repo
    return repo


def _usage(request: Request) -> UsageRepository:
    usage: UsageRepository = request.app.state.usage
    return usage


AdminDep = Annotated[CatalogAdmin, Depends(_admin)]


class CategoryIn(BaseModel):
    name: str


class ProductIn(BaseModel):
    category_id: int
    name: str
    price: Decimal
    description: str = ""
    material: str = ""
    image_url: str | None = None


class ProductPatch(BaseModel):
    name: str | None = None
    price: Decimal | None = None
    description: str | None = None
    material: str | None = None
    image_url: str | None = None
    active: bool | None = None
    category_id: int | None = None


class VariantIn(BaseModel):
    sku: str
    size: str
    color: str
    stock: int = Field(ge=0)


class StockIn(BaseModel):
    stock: int


def _category(c: Category) -> dict[str, Any]:
    return {"id": c.id, "name": c.name}


def _product(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "category_id": p.category_id,
        "name": p.name,
        "description": p.description,
        "material": p.material,
        "price": str(p.price),
        "image_url": p.image_url,
        "active": p.active,
    }


def _variant(v: Variant) -> dict[str, Any]:
    return {
        "id": v.id,
        "product_id": v.product_id,
        "sku": v.sku,
        "size": v.size,
        "color": v.color,
        "stock": v.stock,
    }


@router.get("/categories")
async def list_categories(request: Request) -> list[dict[str, Any]]:
    return [_category(c) for c in await _catalog(request).list_categories()]


@router.post("/categories", status_code=201)
async def create_category(body: CategoryIn, admin: AdminDep) -> dict[str, Any]:
    return _category(await admin.create_category(body.name))


@router.get("/products")
async def list_products(
    admin: AdminDep, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)
) -> list[dict[str, Any]]:
    return [_product(p) for p in await admin.list_products(offset, limit)]


@router.post("/products", status_code=201)
async def create_product(body: ProductIn, admin: AdminDep) -> dict[str, Any]:
    return _product(await admin.create_product(**body.model_dump()))


@router.patch("/products/{product_id}")
async def update_product(product_id: int, body: ProductPatch, admin: AdminDep) -> dict[str, Any]:
    changes = body.model_dump(exclude_unset=True)
    return _product(await admin.update_product(product_id, changes))


@router.get("/products/{product_id}/variants")
async def list_variants(product_id: int, request: Request) -> list[dict[str, Any]]:
    return [_variant(v) for v in await _catalog(request).list_variants(product_id)]


@router.post("/products/{product_id}/variants", status_code=201)
async def create_variant(product_id: int, body: VariantIn, admin: AdminDep) -> dict[str, Any]:
    return _variant(await admin.create_variant(product_id, **body.model_dump()))


@router.patch("/variants/{variant_id}")
async def set_stock(variant_id: int, body: StockIn, admin: AdminDep) -> dict[str, Any]:
    return _variant(await admin.set_stock(variant_id, body.stock))


@router.get("/conversations/{phone}/messages")
async def history(
    phone: str,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    before_id: int | None = None,
) -> list[dict[str, Any]]:
    items = await _messages(request).list_history(phone, limit, before_id)
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "type": m.type,
            "body": m.body,
            "status": m.status,
            "at": m.at.isoformat(),
        }
        for m in items
    ]


@router.get("/stats")
async def stats(request: Request) -> dict[str, Any]:
    summary = await _usage(request).summary()
    return {
        "inbound_messages": summary.inbound_messages,
        "outbound_messages": summary.outbound_messages,
        "customers": summary.customers,
        "top_menu_nodes": [{"node": n, "visits": v} for n, v in summary.top_nodes],
    }

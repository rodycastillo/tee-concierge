"""Typed codes: a customer can type the code of any option, from any screen."""

from datetime import UTC, datetime

import pytest

from tee_concierge.application.engine.engine import MenuEngine
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.messaging import InboundMessage, MessageType, Reply
from tee_concierge.infrastructure.menu.loader import load_menu
from tests.fakes import InMemoryCatalog, InMemoryConversationRepository, RecordingUsage

PHONE = "51922222222"
T0 = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


def _text(text: str) -> InboundMessage:
    return InboundMessage("w", PHONE, MessageType.TEXT, T0, text=text)


@pytest.fixture
def clinic() -> MenuEngine:
    return MenuEngine(
        InMemoryConversationRepository(),
        load_menu("examples/dental-clinic/menu.yaml"),
        InMemoryCatalog(),
        RecordingUsage(),
        clock=lambda: T0,
    )


async def _open(engine: MenuEngine) -> Reply:
    return await engine.reply_to(_text("hola"))


async def test_options_show_their_codes(clinic: MenuEngine) -> None:
    reply = await _open(clinic)

    titles = [o.title for o in reply.options]
    assert titles[0] == "1 🦷 Servicios" and titles[1] == "cita 📅 Agendar una cita"[:24]


async def test_a_nested_code_jumps_straight_to_the_node(clinic: MenuEngine) -> None:
    await _open(clinic)

    reply = await clinic.reply_to(_text("1.2"))

    assert "brackets" in reply.body


async def test_explicit_codes_work_and_ignore_case_and_spaces(clinic: MenuEngine) -> None:
    await _open(clinic)

    assert "Escríbenos con tu nombre" in (await clinic.reply_to(_text(" CITA "))).body
    assert "dolor fuerte" in (await clinic.reply_to(_text("Urgencia"))).body


async def test_zero_always_returns_to_the_main_menu(clinic: MenuEngine) -> None:
    await _open(clinic)
    await clinic.reply_to(_text("1.1"))

    assert "Bienvenido" in (await clinic.reply_to(_text("0"))).body


async def test_menus_list_children_with_navigation(clinic: MenuEngine) -> None:
    await _open(clinic)

    reply = await clinic.reply_to(_text("1"))

    ids = [o.id for o in reply.options]
    assert ids[:3] == [encode("cleaning"), encode("braces"), encode("whitening")]
    assert ids[-2:] == [encode("main"), encode("contact")]


async def test_a_business_without_catalog_has_no_catalog_screens(clinic: MenuEngine) -> None:
    await _open(clinic)

    assert "Bienvenido" in (await clinic.reply_to(_tap_stale())).body


def _tap_stale() -> InboundMessage:
    return InboundMessage("w", PHONE, MessageType.LIST_REPLY, T0, text="x", reply_id="go:cat:1:0")


async def test_placeholders_are_filled_from_the_business(clinic: MenuEngine) -> None:
    await _open(clinic)

    assert "+51900000001" in (await clinic.reply_to(_text("urgencia"))).body
    assert "Lun a Vie" in (await clinic.reply_to(_text("cita"))).body

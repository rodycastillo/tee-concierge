from datetime import UTC, datetime, timedelta

import pytest

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.engine import SESSION_TIMEOUT, MenuEngine
from tee_concierge.application.engine.routing import decode, encode, normalize
from tee_concierge.domain.messaging import InboundMessage, MessageType, Reply
from tests.fakes import InMemoryCatalog, InMemoryConversationRepository, InMemoryFaq

PHONE = "51911111111"
STORE = StoreInfo(name="Tee Concierge", contact_phone="51943713293", hours="Lun a Sáb 10-19")
T0 = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now


def _text(text: str, kind: MessageType = MessageType.TEXT) -> InboundMessage:
    return InboundMessage("w", PHONE, kind, T0, text=text, profile_name="Ana Pérez")


def _tap(option_id: str) -> InboundMessage:
    return InboundMessage("w", PHONE, MessageType.LIST_REPLY, T0, text="x", reply_id=option_id)


def _ids(reply: Reply) -> list[str]:
    return [o.id for o in reply.options]


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def engine(clock: Clock) -> MenuEngine:
    return MenuEngine(
        InMemoryConversationRepository(),
        STORE,
        InMemoryCatalog(),
        InMemoryFaq({"shipping": "Envíos a todo Lima en 24h"}),
        clock=clock,
    )


async def test_first_message_opens_the_main_menu_whatever_it_says(engine: MenuEngine) -> None:
    reply = await engine.reply_to(_text("asdfgh"))

    assert "Bienvenido a Tee Concierge" in reply.body and "Ana" in reply.body
    assert encode("catalog") in _ids(reply) and encode("contact") in _ids(reply)


async def test_hola_returns_to_the_main_menu(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))
    await engine.reply_to(_tap(encode("shipping")))

    reply = await engine.reply_to(_text("¡Hola!"))

    assert "Bienvenido" in reply.body


async def test_tapping_an_option_navigates_and_offers_navigation_back(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))

    reply = await engine.reply_to(_tap(encode("shipping")))

    assert "Lima en 24h" in reply.body  # editable FAQ text wins over the default
    assert _ids(reply) == [encode("main"), encode("contact")]


async def test_keywords_jump_to_nodes_ignoring_accents_and_case(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))

    assert "Lima en 24h" in (await engine.reply_to(_text("¿Cuánto cuesta el ENVÍO?"))).body
    assert "Formas de pago" in (await engine.reply_to(_text("aceptan yape?"))).body
    assert "Contáctanos" in (await engine.reply_to(_text("quiero hablar con un asesor"))).body


async def test_contact_shows_number_and_wa_me_link(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))

    reply = await engine.reply_to(_tap(encode("contact")))

    assert "+51943713293" in reply.body and "https://wa.me/51943713293" in reply.body


async def test_hours_come_from_configuration(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))
    assert "Lun a Sáb 10-19" in (await engine.reply_to(_tap(encode("hours")))).body


async def test_unrecognized_text_reshows_the_current_menu(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))
    await engine.reply_to(_tap(encode("shipping")))

    reply = await engine.reply_to(_text("blablabla"))

    assert reply.body.startswith("No te entendí") and "Lima en 24h" in reply.body
    assert _ids(reply) == [encode("main"), encode("contact")]


async def test_second_misunderstanding_offers_contact(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))
    await engine.reply_to(_text("blabla"))

    reply = await engine.reply_to(_text("sigue sin"))

    assert _ids(reply) == [encode("contact"), encode("main")]


async def test_understanding_resets_the_failure_counter(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))
    await engine.reply_to(_text("blabla"))
    await engine.reply_to(_text("envios"))

    reply = await engine.reply_to(_text("blabla"))

    assert reply.body.startswith("No te entendí")  # not yet the "offer contact" screen


async def test_unsupported_message_gets_a_polite_reply_without_counting_as_failure(
    engine: MenuEngine,
) -> None:
    await engine.reply_to(_text("hola"))
    unsupported = InboundMessage("w", PHONE, MessageType.UNSUPPORTED, T0)

    first = await engine.reply_to(unsupported)
    second = await engine.reply_to(unsupported)

    assert "solo puedo leer" in first.body and "solo puedo leer" in second.body
    assert encode("catalog") in _ids(second)


async def test_stale_or_unknown_option_ids_fall_back_to_the_main_menu(engine: MenuEngine) -> None:
    await engine.reply_to(_text("hola"))

    for stale in ("go:deleted_node", "garbage", "go:"):
        assert "Bienvenido" in (await engine.reply_to(_tap(stale))).body


async def test_a_new_session_after_the_timeout_restarts_at_the_main_menu(
    engine: MenuEngine, clock: Clock
) -> None:
    await engine.reply_to(_text("hola"))
    await engine.reply_to(_tap(encode("shipping")))
    clock.now += SESSION_TIMEOUT + timedelta(minutes=1)

    reply = await engine.reply_to(_text("blabla"))

    assert "Bienvenido" in reply.body


def test_route_encoding_round_trips() -> None:
    assert decode(encode("product", "88", "M")) is not None
    route = decode(encode("product", "88", "M"))
    assert route is not None and (route.node, route.args) == ("product", ("88", "M"))
    assert decode("nonsense") is None


def test_normalize() -> None:
    assert normalize("¿Envíos, ya?") == "envios ya"

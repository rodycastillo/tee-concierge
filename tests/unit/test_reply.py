import pytest

from tee_concierge.domain.messaging import Option, Reply, ReplyKind


def _options(n: int, title: str = "Opción") -> tuple[Option, ...]:
    return tuple(Option(f"go:n{i}", f"{title} {i}") for i in range(n))


def test_kind_depends_on_the_number_of_options() -> None:
    assert Reply("hola").kind is ReplyKind.TEXT
    assert Reply("hola", _options(3)).kind is ReplyKind.BUTTONS
    assert Reply("hola", _options(4)).kind is ReplyKind.LIST
    assert Reply("hola", _options(10)).kind is ReplyKind.LIST


def test_a_description_forces_a_list() -> None:
    assert Reply("hola", (Option("go:a", "A", "detalle"),)).kind is ReplyKind.LIST


@pytest.mark.parametrize(
    "reply",
    [
        lambda: Reply(""),
        lambda: Reply("x" * 1025),
        lambda: Reply("hola", _options(11)),
        lambda: Reply("hola", (Option("go:a", "t" * 21), Option("go:b", "b"))),  # button > 20
        lambda: Reply("hola", _options(4, "t" * 25)),  # row > 24
        lambda: Reply("hola", (Option("go:a", "a"), Option("go:a", "b"))),  # duplicate id
        lambda: Reply("hola", (Option("x" * 201, "a"),)),
    ],
)
def test_whatsapp_limits_are_enforced(reply) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        reply()


def test_button_titles_may_use_the_longer_row_limit_only_in_lists() -> None:
    title = "t" * 24
    assert Reply("hola", _options(4, title[:-2])).kind is ReplyKind.LIST

from pathlib import Path

import pytest

from tee_concierge.application.menu.builder import MenuConfigError, build_menu
from tee_concierge.application.menu.config import MenuConfig
from tee_concierge.application.menu.validation import check_config, resolve_codes
from tee_concierge.infrastructure.menu.loader import load_menu, read_config


def _config(menu: list[dict], **business: object) -> MenuConfig:  # type: ignore[type-arg]
    return MenuConfig.model_validate({"business": {"name": "Demo", **business}, "menu": menu})


def _text(node_id: str, **extra: object) -> dict:  # type: ignore[type-arg]
    return {"id": node_id, "type": "text", "title": node_id.title(), "body": "hola", **extra}


def test_codes_are_positional_unless_given() -> None:
    config = _config(
        [
            {
                "id": "a",
                "type": "menu",
                "title": "A",
                "body": "x",
                "children": [_text("a1"), _text("a2")],
            },
            _text("b", code="envios"),
            _text("c"),
        ]
    )

    assert resolve_codes(config) == {"a": "1", "a1": "1.1", "a2": "1.2", "b": "envios", "c": "3"}


def test_a_valid_config_has_no_problems() -> None:
    assert check_config(_config([_text("a"), _text("b")])) == []


@pytest.mark.parametrize(
    ("menu", "fragment"),
    [
        ([_text("a"), _text("a")], "duplicate id"),
        ([_text("a", code="x"), _text("b", code="X")], "already used"),
        ([_text("a", code="0")], "reserved for the main menu"),
        ([_text("a", code="bad code!")], "must match"),
        ([_text("main")], "reserved id"),
        ([_text("Bad Id")], "id must match"),
        ([_text("a", image_url="http://x/y.png")], "https"),
        (
            [{"id": "m", "type": "menu", "title": "M", "body": "x", "children": []}],
            "at least one child",
        ),
        (
            [
                {"id": "c1", "type": "catalog", "title": "C"},
                {"id": "c2", "type": "catalog", "title": "C"},
            ],
            "at most one 'catalog'",
        ),
        ([_text(f"n{i}") for i in range(11)], "main menu allows"),
        ([], "needs at least one node"),
    ],
)
def test_structural_rules(menu: list[dict], fragment: str) -> None:  # type: ignore[type-arg]
    assert any(fragment in e for e in check_config(_config(menu))), check_config(_config(menu))


def test_submenus_respect_the_whatsapp_list_limit() -> None:
    children = [_text(f"c{i}") for i in range(8)]
    config = _config([{"id": "m", "type": "menu", "title": "M", "body": "x", "children": children}])

    assert any("at most 7" in e for e in check_config(config))


def test_unknown_message_keys_are_rejected() -> None:
    config = _config([_text("a")])
    config.messages["nope"] = "x"

    assert any("unknown keys nope" in e for e in check_config(config))


def test_build_menu_reports_all_problems_at_once() -> None:
    with pytest.raises(MenuConfigError) as raised:
        build_menu(_config([_text("a"), _text("a"), _text("main")]))

    assert len(raised.value.errors) >= 2


def test_schema_errors_and_bad_files_become_config_errors(tmp_path: Path) -> None:
    bad_schema = tmp_path / "bad.yaml"
    bad_schema.write_text("business: {name: X}\nmenu:\n  - {id: a, type: nope, title: A}\n")
    not_yaml = tmp_path / "broken.yaml"
    not_yaml.write_text("a: [unclosed")

    for path in (bad_schema, not_yaml, tmp_path / "missing.yaml"):
        with pytest.raises(MenuConfigError):
            read_config(path)


def test_unknown_fields_are_rejected_so_typos_do_not_pass_silently(tmp_path: Path) -> None:
    path = tmp_path / "typo.yaml"
    path.write_text(
        "business: {name: X, horas: y}\nmenu:\n  - {id: a, type: text, title: A, body: b}\n"
    )

    with pytest.raises(MenuConfigError):
        read_config(path)


def test_environment_overrides_replace_only_non_empty_values() -> None:
    menu = load_menu("examples/dental-clinic/menu.yaml", contact_phone="51911112222")

    assert menu.business.contact_phone == "51911112222"
    assert menu.business.name == "Sonrisa Clara"
    assert menu.business.hours.startswith("Lun a Vie")


def test_messages_can_be_overridden_per_business() -> None:
    menu = load_menu("examples/dental-clinic/menu.yaml")

    assert "cuidar tu sonrisa" in menu.messages.welcome
    assert menu.messages.label_back == "⬅️ Volver"  # untouched defaults remain

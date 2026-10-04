import pytest

from tee_concierge.config import Settings


def test_defaults_do_not_expose_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "super-secret")

    settings = Settings(_env_file=None)

    assert "super-secret" not in repr(settings)
    assert settings.store_name == "Tee Concierge"

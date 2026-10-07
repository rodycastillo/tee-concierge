"""Reads a business's menu file (YAML) and builds the running menu from it."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from tee_concierge.application.menu.builder import Menu, MenuConfigError, build_menu
from tee_concierge.application.menu.config import MenuConfig


def read_config(path: str | Path) -> MenuConfig:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise MenuConfigError([f"cannot read {path}: {error.strerror}"]) from error
    except yaml.YAMLError as error:
        raise MenuConfigError([f"{path} is not valid YAML: {error}"]) from error
    try:
        return MenuConfig.model_validate(raw)
    except ValidationError as error:
        problems = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()]
        raise MenuConfigError(problems) from error


def with_overrides(
    config: MenuConfig, *, name: str = "", contact_phone: str = "", hours: str = ""
) -> MenuConfig:
    """Applies the non-empty environment overrides to the file's business values."""
    changes = {
        k: v for k, v in (("name", name), ("contact_phone", contact_phone), ("hours", hours)) if v
    }
    business = config.business.model_copy(update=changes)
    return config.model_copy(update={"business": business})


def load_menu(
    path: str | Path, *, name: str = "", contact_phone: str = "", hours: str = ""
) -> Menu:
    config = with_overrides(read_config(path), name=name, contact_phone=contact_phone, hours=hours)
    return build_menu(config)

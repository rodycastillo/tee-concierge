"""The shape of a business's menu file. Pure schema; rules live in `validation.py`."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_GREETINGS = [
    "hola", "holi", "buenas", "buenos dias", "buenas tardes", "buenas noches",
    "menu", "inicio", "ayuda", "hello", "hi",
]  # fmt: skip


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BusinessConfig(_Strict):
    name: str
    contact_phone: str = ""  # digits with country code; prefer the STORE_CONTACT_PHONE env var
    hours: str = ""
    show_codes: bool = True  # prefix option titles with their code
    greeting_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_GREETINGS))

    @field_validator("contact_phone", mode="before")
    @classmethod
    def _phone_as_text(cls, value: object) -> object:
        return str(value) if isinstance(value, int) else value


class _Node(_Strict):
    id: str
    title: str
    code: str | None = None
    keywords: list[str] = Field(default_factory=list)


class TextNode(_Node):
    type: Literal["text"]
    body: str
    image_url: str | None = None


class ContactNode(_Node):
    type: Literal["contact"]
    body: str | None = None  # defaults to the standard contact message


class CatalogNode(_Node):
    type: Literal["catalog"]


class MenuNode(_Node):
    type: Literal["menu"]
    body: str
    children: list["NodeConfig"]


NodeConfig = Annotated[TextNode | ContactNode | CatalogNode | MenuNode, Field(discriminator="type")]
MenuNode.model_rebuild()


class MenuConfig(_Strict):
    business: BusinessConfig
    menu: list[NodeConfig]  # children of the main menu
    messages: dict[str, str] = Field(default_factory=dict)

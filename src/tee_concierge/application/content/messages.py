"""Customer-facing text. Spanish defaults; a business can override any field in its config.

Templates use `{placeholders}`; unknown placeholders are left untouched, so a stray brace in
a business's copy can never raise an error in front of a customer.
"""

import re
from dataclasses import dataclass, fields

_TOKEN = re.compile(r"\{(\w+)\}")


def fill(template: str, **values: object) -> str:
    return _TOKEN.sub(
        lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), template
    )


@dataclass(frozen=True, slots=True)
class Messages:
    # Navigation labels (buttons allow 20 chars, list rows 24)
    label_back: str = "⬅️ Volver"
    label_main: str = "🏠 Menú principal"
    label_contact: str = "📞 Contáctanos"
    label_more: str = "➡️ Ver más"
    label_sizes_colors: str = "📏 Tallas y colores"
    label_other_size: str = "⬅️ Otra talla"
    list_button: str = "Ver opciones"

    # Conversation
    welcome: str = "¡Hola! 👋 Bienvenido a {business}. ¿En qué te puedo ayudar?"
    welcome_named: str = "¡Hola, {name}! 👋 Bienvenido a {business}. ¿En qué te puedo ayudar?"
    not_understood: str = "No te entendí 😅 Por favor elige una de las opciones:"
    not_understood_twice: str = (
        "Sigo sin entenderte 😅 Si prefieres, puedes hablar directamente con nosotros "
        "o volver al menú principal."
    )
    unsupported: str = "Por ahora solo puedo leer texto y opciones 🙂 Elige una de las opciones:"
    error_generic: str = "Tuvimos un problema 😕 Intenta de nuevo o contáctanos."

    # Contact node default text
    contact: str = "📞 *Contáctanos*\n\nEscríbenos o llámanos al +{phone}.\nChatea directo: {link}"
    contact_missing: str = "📞 *Contáctanos*\n\nPronto tendremos un número de contacto disponible."

    # Catalog node
    catalog_choose_category: str = "👕 *Nuestro catálogo*\n\nElige una categoría:"
    catalog_empty: str = "Por ahora no tenemos productos disponibles. Vuelve pronto 👕"
    not_available: str = "Ese producto ya no está disponible 😕 Mira nuestro catálogo:"
    choose_product: str = "👕 *{category}*{page}\n\nElige un producto:"
    page_suffix: str = " (página {page} de {pages})"
    choose_size: str = "📏 *{product}*\n\nElige tu talla:"
    size_label: str = "Talla {size}"
    stock_header: str = "*{product}* · Talla {size}"
    stock_available: str = "disponible"
    stock_low: str = "¡últimas unidades!"
    stock_out: str = "agotado"
    size_sold_out: str = "Agotada"

    @classmethod
    def with_overrides(cls, overrides: dict[str, str]) -> "Messages":
        unknown = set(overrides) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"unknown message keys: {', '.join(sorted(unknown))}")
        return cls(**overrides)

    @classmethod
    def keys(cls) -> set[str]:
        return {f.name for f in fields(cls)}

"""All customer-facing Spanish copy. Nothing else in the codebase hardcodes user text.

FAQ answers below are generic placeholders until the store owner supplies real policies.
"""

from tee_concierge.application.content.store import StoreInfo

# Menu labels (list rows allow 24 chars, buttons 20)
LABEL_CATALOG = "👕 Ver catálogo"
LABEL_SIZES = "📏 Guía de tallas"
LABEL_SHIPPING = "🚚 Envíos"
LABEL_PAYMENT = "💳 Formas de pago"
LABEL_RETURNS = "🔁 Cambios/devoluciones"
LABEL_HOURS = "🕒 Horarios y ubicación"
LABEL_CONTACT = "📞 Contáctanos"
LABEL_BACK = "⬅️ Volver"
LABEL_MAIN = "🏠 Menú principal"
LABEL_MORE = "➡️ Ver más"
LABEL_SIZES_COLORS = "📏 Tallas y colores"
LABEL_OTHER_SIZE = "⬅️ Otra talla"
LIST_BUTTON = "Ver opciones"

NOT_UNDERSTOOD = "No te entendí 😅 Por favor elige una de las opciones:"
NOT_UNDERSTOOD_TWICE = (
    "Sigo sin entenderte 😅 Si prefieres, puedes hablar directamente con nosotros "
    "o volver al menú principal."
)
UNSUPPORTED = "Por ahora solo puedo leer texto y opciones 🙂 Elige una de las opciones:"

SIZES = "📏 *Guía de tallas*\n\nEscríbenos y te ayudamos a elegir la talla ideal según tus medidas."
SHIPPING = (
    "🚚 *Envíos*\n\nEl costo y el tiempo de entrega dependen de tu ubicación. "
    "Contáctanos y te cotizamos."
)
PAYMENT = "💳 *Formas de pago*\n\nConsúltanos por los medios de pago disponibles."
RETURNS = (
    "🔁 *Cambios y devoluciones*\n\nSi tu pedido tiene algún problema, contáctanos y lo resolvemos."
)


def welcome(store: StoreInfo, first_name: str | None) -> str:
    greeting = f"¡Hola, {first_name}! 👋" if first_name else "¡Hola! 👋"
    return f"{greeting} Bienvenido a {store.name}. ¿En qué te puedo ayudar?"


def hours(store: StoreInfo) -> str:
    if store.hours:
        return f"🕒 *Horarios*\n\n{store.hours}"
    return "🕒 *Horarios y ubicación*\n\nEscríbenos para conocer nuestro horario y ubicación."


def contact(store: StoreInfo) -> str:
    if not store.contact_phone:
        return "📞 *Contáctanos*\n\nPronto tendremos un número de contacto disponible."
    return (
        f"📞 *Contáctanos*\n\nEscríbenos o llámanos al +{store.contact_phone}.\n"
        f"Chatea directo: {store.whatsapp_link}"
    )


CATALOG_EMPTY = "Por ahora no tenemos productos disponibles. Vuelve pronto 👕"
CATALOG_CHOOSE_CATEGORY = "👕 *Nuestro catálogo*\n\nElige una categoría:"
NOT_AVAILABLE = "Ese producto ya no está disponible 😕 Mira nuestro catálogo:"


def choose_product(category: str, page: int, pages: int) -> str:
    suffix = f" (página {page + 1} de {pages})" if pages > 1 else ""
    return f"👕 *{category}*{suffix}\n\nElige un producto:"


def product_detail(name: str, price: str, material: str, description: str) -> str:
    lines = [f"*{name}*", f"💰 {price}"]
    if material:
        lines.append(f"🧵 {material}")
    if description:
        lines.append(f"\n{description}")
    return "\n".join(lines)


def choose_size(name: str) -> str:
    return f"📏 *{name}*\n\nElige tu talla:"


def stock_for_size(name: str, size: str, lines: list[str]) -> str:
    return f"*{name}* · Talla {size}\n\n" + "\n".join(lines)


STOCK_AVAILABLE = "disponible"
STOCK_LOW = "¡últimas unidades!"
STOCK_OUT = "agotado"
SIZE_SOLD_OUT = "Agotada"

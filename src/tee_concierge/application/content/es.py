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
LIST_BUTTON = "Ver opciones"

NOT_UNDERSTOOD = "No te entendí 😅 Por favor elige una de las opciones:"
NOT_UNDERSTOOD_TWICE = (
    "Sigo sin entenderte 😅 Si prefieres, puedes hablar directamente con nosotros "
    "o volver al menú principal."
)
UNSUPPORTED = "Por ahora solo puedo leer texto y opciones 🙂 Elige una de las opciones:"

CATALOG = "Muy pronto podrás ver aquí nuestro catálogo de polos. 👕"
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

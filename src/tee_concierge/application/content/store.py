from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoreInfo:
    name: str
    contact_phone: str = ""  # digits with country code, e.g. 51943713293
    hours: str = ""

    @property
    def whatsapp_link(self) -> str | None:
        return f"https://wa.me/{self.contact_phone}" if self.contact_phone else None

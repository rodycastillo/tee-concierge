import httpx

from tee_concierge.domain.messaging import Reply
from tee_concierge.infrastructure.whatsapp.payloads import build_send_payload


class WhatsAppCloudGateway:
    """Sends messages through the Meta WhatsApp Cloud API."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        phone_number_id: str,
        access_token: str,
        api_version: str = "v21.0",
    ) -> None:
        self._http = http
        self._url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        self._headers = {"Authorization": f"Bearer {access_token}"}

    async def send(self, to: str, reply: Reply) -> str | None:
        response = await self._http.post(
            self._url, headers=self._headers, json=build_send_payload(to, reply)
        )
        response.raise_for_status()
        messages = response.json().get("messages") or []
        return messages[0].get("id") if messages else None

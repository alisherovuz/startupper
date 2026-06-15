"""
Telegram Bot API wrapper (replaces src/Core/Telegram.php).
Async, backed by a single shared httpx client.
"""
import httpx

from . import config


class TelegramError(Exception):
    pass


class Telegram:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def request(self, method: str, params: dict | None = None):
        params = params or {}
        resp = await self.client.post(self.api_url + method, json=params)
        data = resp.json()
        if not data.get("ok"):
            raise TelegramError(
                f"Telegram API error ({method}): {data.get('description', 'Unknown error')}"
            )
        return data.get("result", True)

    async def send_message(self, chat_id, text: str, **options) -> dict:
        params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", **options}
        result = await self.request("sendMessage", params)
        return result if isinstance(result, dict) else {}

    async def send_message_with_keyboard(
        self, chat_id, text: str, keyboard: list, inline: bool = True
    ) -> dict:
        if inline:
            reply_markup = {"inline_keyboard": keyboard}
        else:
            reply_markup = {
                "keyboard": keyboard,
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
        return await self.send_message(chat_id, text, reply_markup=reply_markup)

    async def edit_message(self, chat_id, message_id: int, text: str, keyboard=None) -> dict:
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if keyboard is not None:
            params["reply_markup"] = {"inline_keyboard": keyboard}
        result = await self.request("editMessageText", params)
        return result if isinstance(result, dict) else {}

    async def answer_callback(self, callback_id: str, text: str = "", show_alert: bool = False) -> bool:
        try:
            await self.request(
                "answerCallbackQuery",
                {"callback_query_id": callback_id, "text": text, "show_alert": show_alert},
            )
            return True
        except TelegramError:
            return False

    async def delete_message(self, chat_id, message_id: int) -> bool:
        try:
            await self.request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
            return True
        except TelegramError:
            return False

    async def send_to_channel(self, channel_id: str, text: str, keyboard=None) -> dict:
        params = {"chat_id": channel_id, "text": text, "parse_mode": "HTML"}
        if keyboard:
            params["reply_markup"] = {"inline_keyboard": keyboard}
        result = await self.request("sendMessage", params)
        return result if isinstance(result, dict) else {}

    async def set_webhook(self, url: str) -> bool:
        params = {"url": url, "allowed_updates": ["message", "callback_query"]}
        if config.WEBHOOK_SECRET:
            params["secret_token"] = config.WEBHOOK_SECRET
        return bool(await self.request("setWebhook", params))

    async def get_webhook_info(self) -> dict:
        result = await self.request("getWebhookInfo")
        return result if isinstance(result, dict) else {}

    async def set_my_commands(self, commands: list) -> bool:
        return bool(await self.request("setMyCommands", {"commands": commands}))

    async def remove_keyboard(self, chat_id, text: str) -> dict:
        return await self.send_message(chat_id, text, reply_markup={"remove_keyboard": True})

    async def get_chat_member(self, chat_id: str, user_id: int) -> str:
        result = await self.request("getChatMember", {"chat_id": chat_id, "user_id": user_id})
        return result.get("status", "left") if isinstance(result, dict) else "left"

    async def send_photo(self, chat_id, photo: str, caption: str = "", **options) -> dict:
        params = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": "HTML",
            **options,
        }
        result = await self.request("sendPhoto", params)
        return result if isinstance(result, dict) else {}

    async def send_photo_with_keyboard(self, chat_id, photo: str, caption: str, keyboard: list) -> dict:
        return await self.send_photo(
            chat_id, photo, caption, reply_markup={"inline_keyboard": keyboard}
        )

    async def send_document(self, chat_id, content: bytes, filename: str, caption: str = "") -> dict:
        """Upload a file (multipart/form-data) — used by /export for the .xlsx."""
        files = {
            "document": (
                filename,
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
        resp = await self.client.post(self.api_url + "sendDocument", data=data, files=files)
        j = resp.json()
        if not j.get("ok"):
            raise TelegramError(f"sendDocument error: {j.get('description', 'Unknown error')}")
        return j.get("result", {})

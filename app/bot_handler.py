"""
Core bot logic — a faithful port of src/Bot/BotHandler.php.

A fresh BotHandler is created per update (mirroring PHP's per-request model),
so self.user / self.state are scoped to a single update.
"""
import html
from datetime import datetime, timedelta

from . import config, db, lang
from . import settings as Settings
from .telegram import Telegram, TelegramError


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


class BotHandler:
    def __init__(self, telegram: Telegram):
        self.telegram = telegram
        self.update: dict = {}
        self.user: dict | None = None
        self.state: dict | None = None

    async def handle(self, update: dict):
        self.update = update
        try:
            if "message" in update:
                await self.handle_message(update["message"])
            elif "callback_query" in update:
                await self.handle_callback(update["callback_query"])
        except Exception as e:  # noqa: BLE001
            print(f"Bot error: {e}")

    # ==================== MESSAGE ROUTING ====================

    async def handle_message(self, message: dict):
        chat_id = message["chat"]["id"]
        text = message.get("text", "") or ""
        from_ = message["from"]
        photo = message.get("photo")

        self.user = await self.get_or_create_user(from_)

        if self.user["is_banned"]:
            return

        lang.set_lang(self.user.get("language_code") or "uz")

        # Step 1: language selection
        if not self.user.get("language_code") or self.user["language_code"] == "new":
            await self.show_language_selection(chat_id)
            return

        # Step 2: channel subscription
        if not await self.check_subscription(chat_id):
            return

        # Step 3: registration
        if not self.user["is_registered"]:
            self.state = await self.get_state(from_["id"])
            if not self.state or not self.state["state"].startswith("reg:"):
                await self.start_registration(chat_id)
                return
            await self.handle_registration_input(chat_id, text)
            return

        self.state = await self.get_state(from_["id"])

        # Photo upload for event creation
        if photo and self.state and self.state["state"] == "admin:event_image":
            await self.handle_event_photo(chat_id, photo)
            return

        if text.startswith("/"):
            await self.handle_command(chat_id, text)
            return

        if self.state and self.state["state"] != "idle":
            await self.handle_state_input(chat_id, text)
            return

    # ==================== SUBSCRIPTION ====================

    async def check_subscription(self, chat_id: int) -> bool:
        require_sub = await Settings.get("require_subscription", "1")
        if require_sub not in ("1", 1, True):
            return True

        channels = config.REQUIRED_CHANNELS
        if not channels:
            return True

        not_subscribed = []
        for channel in channels:
            try:
                status = await self.telegram.get_chat_member(channel["id"], self.user["telegram_id"])
                if status not in ("member", "administrator", "creator"):
                    not_subscribed.append(channel)
            except TelegramError:
                not_subscribed.append(channel)

        if not not_subscribed:
            return True

        await self.show_subscription_required(chat_id, not_subscribed)
        return False

    async def show_subscription_required(self, chat_id: int, channels: list):
        text = lang.get("subscription_required")
        keyboard = []
        for channel in channels:
            uname = channel["username"]
            keyboard.append([{"text": "📢 " + uname, "url": "https://t.me/" + uname.lstrip("@")}])
        keyboard.append([{"text": lang.get("btn_check_subscription"), "callback_data": "check_sub"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    # ==================== REGISTRATION ====================

    async def start_registration(self, chat_id: int):
        await self.telegram.send_message(chat_id, lang.get("registration_welcome"))
        await self.set_state(self.user["telegram_id"], "reg:full_name")
        await self.telegram.send_message(chat_id, lang.get("reg_ask_full_name"))

    async def handle_registration_input(self, chat_id: int, text: str):
        state = self.state["state"]
        data = self.state.get("data") or {}

        if state == "reg:full_name":
            if len(text) < 3 or len(text) > 100:
                await self.telegram.send_message(chat_id, lang.get("reg_name_error"))
                return
            data["full_name"] = text
            await self.set_state(self.user["telegram_id"], "reg:age", data)
            await self.telegram.send_message(chat_id, lang.get("reg_ask_age"))

        elif state == "reg:age":
            try:
                age = int(text)
            except ValueError:
                age = 0
            if age < 14 or age > 80:
                await self.telegram.send_message(chat_id, lang.get("reg_age_error"))
                return
            data["age"] = age
            await self.set_state(self.user["telegram_id"], "reg:city", data)
            await self.show_city_selection(chat_id)

        elif state == "reg:city":
            data["city"] = text
            await self.set_state(self.user["telegram_id"], "reg:profession", data)
            await self.telegram.send_message(chat_id, lang.get("reg_ask_profession"))

        elif state == "reg:profession":
            data["profession"] = text
            await db.update(
                "users",
                {
                    "full_name": data["full_name"],
                    "age": data["age"],
                    "city": data["city"],
                    "profession": data["profession"],
                    "is_registered": 1,
                },
                "id = ?",
                self.user["id"],
            )
            await self.set_state(self.user["telegram_id"], "idle")
            await self.telegram.send_message(chat_id, lang.get("reg_success"))
            self.user["is_registered"] = 1
            await self.cmd_start(chat_id)

    async def show_city_selection(self, chat_id: int):
        keyboard = [
            [{"text": "🏙 Toshkent", "callback_data": "reg_city:Toshkent"},
             {"text": "🏙 Samarqand", "callback_data": "reg_city:Samarqand"}],
            [{"text": "🏙 Buxoro", "callback_data": "reg_city:Buxoro"},
             {"text": "🏙 Namangan", "callback_data": "reg_city:Namangan"}],
            [{"text": "🏙 Andijon", "callback_data": "reg_city:Andijon"},
             {"text": "🏙 Farg'ona", "callback_data": "reg_city:Fargona"}],
            [{"text": "🏙 Qarshi", "callback_data": "reg_city:Qarshi"},
             {"text": "🏙 Nukus", "callback_data": "reg_city:Nukus"}],
            [{"text": "🌍 Boshqa", "callback_data": "reg_city:other"}],
        ]
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("reg_ask_city"), keyboard)

    # ==================== LANGUAGE SELECTION ====================

    async def show_language_selection(self, chat_id: int):
        text = (
            "🌐 <b>Tilni tanlang / Choose your language</b>\n\n"
            "Iltimos, o'zingizga qulay tilni tanlang:\n"
            "Please select your preferred language:"
        )
        keyboard = [[
            {"text": "🇺🇿 O'zbek", "callback_data": "lang:uz"},
            {"text": "🇺🇸 English", "callback_data": "lang:en"},
        ]]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    # ==================== COMMANDS ====================

    async def handle_command(self, chat_id: int, text: str):
        command = text.split(" ")[0].split("@")[0]

        if text.startswith("/start "):
            param = text[7:].strip()
            if param.startswith("apply_"):
                request_id = param.replace("apply_", "")
                await self.handle_respond_callback(chat_id, 0, request_id)
                return

        handlers = {
            "/start": self.cmd_start,
            "/help": self.cmd_help,
            "/find": self.cmd_find_teammate,
            "/post": self.cmd_post_request,
            "/my_requests": self.cmd_my_requests,
            "/resources": self.cmd_resources,
            "/profile": self.cmd_profile,
            "/language": self.show_language_selection,
            "/cancel": self.cmd_cancel,
            "/admin": self.cmd_admin,
        }
        if command == "/skip":
            return
        handler = handlers.get(command)
        if handler:
            await handler(chat_id)
        else:
            await self.telegram.send_message(chat_id, lang.get("unknown_command"))

    async def cmd_start(self, chat_id: int):
        name = self.user.get("full_name") or self.user["first_name"]
        text = lang.get("welcome_title", name) + "\n\n"
        text += lang.get("welcome_message") + "\n\n"
        text += lang.get("what_to_do")

        keyboard = [
            [{"text": lang.get("btn_find_teammate"), "callback_data": "menu:find"},
             {"text": lang.get("btn_post_request"), "callback_data": "menu:post"}],
            [{"text": lang.get("btn_events"), "callback_data": "menu:events"},
             {"text": lang.get("btn_resources"), "callback_data": "menu:resources"}],
            [{"text": lang.get("btn_my_profile"), "callback_data": "menu:profile"},
             {"text": lang.get("btn_my_requests"), "callback_data": "menu:my_requests"}],
            [{"text": "📝 Ariza topshirish", "callback_data": "app:start"}],
            [{"text": lang.get("btn_change_language"), "callback_data": "menu:language"}],
        ]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def cmd_help(self, chat_id: int):
        await self.telegram.send_message(chat_id, lang.get("help_title") + lang.get("help_commands"))

    async def cmd_find_teammate(self, chat_id: int):
        categories = await db.fetch_all(
            """SELECT c.*, COUNT(r.id) as count
               FROM teammate_categories c
               INNER JOIN teammate_requests r ON c.id = r.category_id AND r.status = 'approved'
               WHERE c.is_active = 1
               GROUP BY c.id
               HAVING COUNT(r.id) > 0
               ORDER BY c.sort_order"""
        )
        if not categories:
            await self.telegram.send_message(chat_id, lang.get("no_requests_available"))
            return

        keyboard = []
        for cat in categories:
            keyboard.append([{
                "text": f"{cat['icon']} {cat['name']} ({cat['count']})",
                "callback_data": f"find:{cat['id']}",
            }])
        keyboard.append([{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}])
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("find_title"), keyboard)

    async def cmd_post_request(self, chat_id: int):
        max_requests = await Settings.get("max_active_requests", 3)
        active_count = await db.count(
            "teammate_requests",
            "user_id = ? AND status IN ('pending', 'approved')",
            self.user["id"],
        )
        if active_count >= int(max_requests):
            await self.telegram.send_message(chat_id, lang.get("max_requests_reached", int(max_requests)))
            return

        categories = await db.fetch_all(
            "SELECT * FROM teammate_categories WHERE is_active = 1 ORDER BY sort_order"
        )
        keyboard = []
        for cat in categories:
            keyboard.append([{
                "text": f"{cat['icon']} {cat['name']}",
                "callback_data": f"new_req:cat:{cat['id']}",
            }])
        keyboard.append([{"text": lang.get("cancel"), "callback_data": "menu:main"}])
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("post_title"), keyboard)

    async def cmd_my_requests(self, chat_id: int):
        requests = await db.fetch_all(
            """SELECT r.*, c.name as category_name, c.icon
               FROM teammate_requests r
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.user_id = ?
               ORDER BY r.created_at DESC
               LIMIT 10""",
            self.user["id"],
        )
        if not requests:
            await self.telegram.send_message(chat_id, lang.get("no_requests_yet"))
            return

        status_icon = {"pending": "🟡", "approved": "🟢", "rejected": "🔴", "closed": "⚫"}
        keyboard = []
        for req in requests:
            icon = status_icon.get(req["status"], "⚪")
            keyboard.append([{
                "text": f"{icon} {req['icon']} " + req["title"][:30],
                "callback_data": f"my_req:{req['id']}",
            }])
        keyboard.append([{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}])
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("my_requests_title"), keyboard)

    async def cmd_resources(self, chat_id: int):
        categories = await db.fetch_all(
            """SELECT rc.*, COUNT(r.id) as count
               FROM resource_categories rc
               INNER JOIN resources r ON rc.id = r.category_id AND r.is_active = 1
               WHERE rc.is_active = 1
               GROUP BY rc.id
               HAVING COUNT(r.id) > 0
               ORDER BY rc.sort_order"""
        )
        if not categories:
            await self.telegram.send_message(chat_id, lang.get("no_resources_available"))
            return

        keyboard = []
        for cat in categories:
            keyboard.append([{
                "text": f"{cat['icon']} {cat['name']} ({cat['count']})",
                "callback_data": f"res:{cat['id']}",
            }])
        keyboard.append([{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}])
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("resources_title"), keyboard)

    async def cmd_events(self, chat_id: int):
        await self.show_browse_card(chat_id, None, "evt", 0)

    # ==================== CAROUSEL BROWSING ====================

    async def handle_browse_callback(self, chat_id: int, message_id: int, params: str):
        parts = params.split(":")
        kind = parts[0] if parts else ""
        if kind == "evt":
            index = int(parts[1]) if len(parts) > 1 else 0
            await self.telegram.delete_message(chat_id, message_id)
            await self.show_browse_card(chat_id, None, "evt", index)
        elif kind == "req":
            cat_id = int(parts[1]) if len(parts) > 1 else 0
            index = int(parts[2]) if len(parts) > 2 else 0
            await self.telegram.delete_message(chat_id, message_id)
            await self.show_browse_card(chat_id, cat_id, "req", index)

    async def fetch_browse_items(self, kind: str, cat_id: int | None) -> list:
        if kind == "evt":
            return await db.fetch_all(
                "SELECT * FROM events WHERE is_active = 1 AND event_date >= ? "
                "ORDER BY event_date ASC LIMIT 10",
                datetime.now(),
            )
        return await db.fetch_all(
            """SELECT r.*, u.first_name, u.username, u.company_name, u.full_name,
                      c.icon, c.name as category_name
               FROM teammate_requests r
               JOIN users u ON r.user_id = u.id
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.category_id = ? AND r.status = 'approved'
               ORDER BY r.created_at DESC LIMIT 10""",
            cat_id,
        )

    async def show_browse_card(self, chat_id: int, cat_id: int | None, kind: str, index: int):
        items = await self.fetch_browse_items(kind, cat_id)
        if not items:
            keyboard = [[{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}]]
            msg = lang.get("no_events") if kind == "evt" else lang.get("no_requests_in_category")
            await self.telegram.send_message_with_keyboard(chat_id, msg, keyboard)
            return

        total = len(items)
        index = max(0, min(index, total - 1))
        item = items[index]

        if kind == "evt":
            text, photo, action_row = self.render_event_content(item)
            nav_prefix = "browse:evt"
        else:
            text, photo, action_row = self.render_request_content(item)
            nav_prefix = f"browse:req:{cat_id}"

        nav = []
        if total > 1:
            prev = (index - 1 + total) % total
            nxt = (index + 1) % total
            nav = [
                {"text": "◀️", "callback_data": f"{nav_prefix}:{prev}"},
                {"text": f"{index + 1}/{total}", "callback_data": "browse:noop"},
                {"text": "▶️", "callback_data": f"{nav_prefix}:{nxt}"},
            ]

        keyboard = []
        if nav:
            keyboard.append(nav)
        if action_row:
            keyboard.append(action_row)
        keyboard.append([{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}])

        limit = 1024 if photo else 4096
        if len(text) > limit:
            text = text[: limit - 2] + "…"

        if photo:
            await self.telegram.send_photo_with_keyboard(chat_id, photo, text, keyboard)
        else:
            await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    def render_event_content(self, event: dict):
        date = event["event_date"]
        date_str = date.strftime("%d.%m.%Y %H:%M") if isinstance(date, datetime) else str(date)

        text = "🎯 <b>" + esc(event["title"]) + "</b>\n\n"
        text += esc(event["description"]) + "\n\n"
        text += lang.get("event_date") + f" {date_str}"
        if event.get("location"):
            text += "\n" + lang.get("event_location") + " " + esc(event["location"])

        action = []
        if event.get("registration_url"):
            action.append({"text": lang.get("btn_register_event"), "url": event["registration_url"]})
        return text, event.get("image_file_id"), action

    def render_request_content(self, req: dict):
        poster_name = req.get("full_name") or req["first_name"]
        text = f"{req['icon']} <b>" + esc(req["title"]) + "</b>\n\n"
        text += lang.get("posted_by") + " " + esc(poster_name)
        if req.get("company_name"):
            text += " @ " + esc(req["company_name"])
        text += "\n\n📝 " + esc(req["description"]) + "\n\n"
        if req.get("requirements"):
            text += lang.get("requirements") + " " + esc(req["requirements"]) + "\n\n"
        text += lang.get("compensation") + " " + lang.get_compensation_type(req["compensation_type"])
        if req.get("compensation_details"):
            text += " - " + esc(req["compensation_details"])
        text += "\n" + lang.get("location") + " " + lang.get_location_type(req["location_type"])

        action = [{"text": lang.get("btn_interested"), "callback_data": f"respond:{req['id']}"}]
        return text, None, action

    # ==================== PROFILE ====================

    async def cmd_profile(self, chat_id: int):
        u = self.user
        text = lang.get("profile_title")
        full = u.get("full_name") or (u["first_name"] + " " + (u.get("last_name") or ""))
        text += lang.get("profile_name") + " " + full + "\n"
        text += lang.get("profile_username") + " @" + (u.get("username") or lang.get("not_set")) + "\n"
        text += "📅 " + lang.get("profile_age") + " " + str(u.get("age") or lang.get("not_set")) + "\n"
        text += "🏙 " + lang.get("profile_city") + " " + str(u.get("city") or lang.get("not_set")) + "\n"
        text += "💼 " + lang.get("profile_profession") + " " + str(u.get("profession") or lang.get("not_set")) + "\n"
        text += lang.get("profile_company") + " " + (u.get("company_name") or lang.get("not_set")) + "\n"
        text += lang.get("profile_bio") + " " + (u.get("bio") or lang.get("not_set")) + "\n"

        keyboard = [
            [{"text": lang.get("btn_edit_profile"), "callback_data": "profile:edit"}],
            [{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}],
        ]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def cmd_cancel(self, chat_id: int):
        await self.set_state(self.user["telegram_id"], "idle")
        await self.telegram.remove_keyboard(chat_id, lang.get("action_cancelled"))

    # ==================== CALLBACK ROUTING ====================

    async def handle_callback(self, callback: dict):
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        data = callback["data"]
        from_ = callback["from"]

        self.user = await self.get_or_create_user(from_)
        lang.set_lang(self.user.get("language_code") or "uz")
        await self.telegram.answer_callback(callback["id"])

        if data == "check_sub":
            if await self.check_subscription(chat_id):
                if not self.user["is_registered"]:
                    await self.start_registration(chat_id)
                else:
                    await self.cmd_start(chat_id)
            return

        if data.startswith("reg_city:"):
            await self.handle_reg_city_callback(chat_id, data)
            return

        if not await self.check_subscription(chat_id):
            return

        action, params = self.parse_callback(data)
        routes = {
            "lang": lambda: self.handle_language_callback(chat_id, params),
            "menu": lambda: self.handle_menu_callback(chat_id, message_id, params),
            "find": lambda: self.handle_find_callback(chat_id, message_id, params),
            "new_req": lambda: self.handle_new_request_callback(chat_id, message_id, params),
            "my_req": lambda: self.handle_my_request_callback(chat_id, message_id, params),
            "res": lambda: self.handle_resource_callback(chat_id, message_id, params),
            "profile": lambda: self.handle_profile_callback(chat_id, message_id, params),
            "respond": lambda: self.handle_respond_callback(chat_id, message_id, params),
            "browse": lambda: self.handle_browse_callback(chat_id, message_id, params),
            "admin": lambda: self.handle_admin_callback(chat_id, message_id, params),
        }
        route = routes.get(action)
        if route:
            await route()

    async def handle_reg_city_callback(self, chat_id: int, data: str):
        city = data.replace("reg_city:", "")
        self.state = await self.get_state(self.user["telegram_id"])
        state_data = (self.state or {}).get("data") or {}

        if city == "other":
            await self.telegram.send_message(chat_id, lang.get("reg_type_city"))
            return

        state_data["city"] = city
        await self.set_state(self.user["telegram_id"], "reg:profession", state_data)
        await self.telegram.send_message(chat_id, lang.get("reg_ask_profession"))

    async def handle_language_callback(self, chat_id: int, lang_code: str):
        await db.update("users", {"language_code": lang_code}, "id = ?", self.user["id"])
        self.user["language_code"] = lang_code
        lang.set_lang(lang_code)
        await self.telegram.send_message(chat_id, lang.get("language_set"))

        if not await self.check_subscription(chat_id):
            return
        if not self.user["is_registered"]:
            await self.start_registration(chat_id)
            return
        await self.cmd_start(chat_id)

    async def handle_menu_callback(self, chat_id: int, message_id: int, params: str):
        routes = {
            "main": self.cmd_start,
            "find": self.cmd_find_teammate,
            "post": self.cmd_post_request,
            "events": self.cmd_events,
            "resources": self.cmd_resources,
            "profile": self.cmd_profile,
            "my_requests": self.cmd_my_requests,
            "language": self.show_language_selection,
        }
        handler = routes.get(params)
        if handler:
            await handler(chat_id)

    async def handle_find_callback(self, chat_id: int, message_id: int, params: str):
        await self.show_browse_card(chat_id, int(params), "req", 0)

    async def handle_new_request_callback(self, chat_id: int, message_id: int, params: str):
        type_, value = params.split(":", 1)

        if type_ == "cat":
            category_id = int(value)
            category = await db.fetch("SELECT * FROM teammate_categories WHERE id = ?", category_id)
            if category and category["slug"] == "other":
                await self.set_state(self.user["telegram_id"], "new_req:custom_cat", {"category_id": category_id})
                await self.telegram.send_message(chat_id, lang.get("other_category_prompt"))
                return
            await self.set_state(self.user["telegram_id"], "new_req:title", {"category_id": category_id})
            await self.telegram.send_message(chat_id, lang.get("step_title", category["name"]))

        elif type_ == "comp":
            self.state = await self.get_state(self.user["telegram_id"])
            data = (self.state or {}).get("data") or {}
            data["compensation_type"] = value
            await self.set_state(self.user["telegram_id"], "new_req:comp_details", data)
            await self.telegram.send_message(
                chat_id, lang.get("step_compensation_details", value.capitalize())
            )

        elif type_ == "loc":
            self.state = await self.get_state(self.user["telegram_id"])
            data = (self.state or {}).get("data") or {}
            data["location_type"] = value
            expiry_days = int(await Settings.get("request_expiry_days", 30))

            await db.insert("teammate_requests", {
                "user_id": self.user["id"],
                "category_id": data["category_id"],
                "custom_category": data.get("custom_category"),
                "title": data["title"],
                "description": data["description"],
                "requirements": data.get("requirements"),
                "compensation_type": data.get("compensation_type", "negotiable"),
                "compensation_details": data.get("compensation_details"),
                "location_type": value,
                "status": "pending",
                "expires_at": datetime.now() + timedelta(days=expiry_days),
            })
            await self.set_state(self.user["telegram_id"], "idle")
            await self.telegram.send_message(chat_id, lang.get("request_submitted", data["title"]))

            admin_chat_id = await Settings.get("admin_chat_id") or config.ADMIN_CHAT_ID
            if admin_chat_id:
                try:
                    uname = self.user.get("username") or ""
                    await self.telegram.send_message(
                        admin_chat_id,
                        "📬 <b>Yangi e'lon!</b>\n\n"
                        f"👤 {self.user.get('full_name') or self.user['first_name']} (@{uname})\n"
                        f"📝 {data['title']}\n\n"
                        "Admin panelda ko'ring.",
                    )
                except TelegramError:
                    pass

    # ==================== STATE INPUT ====================

    async def handle_state_input(self, chat_id: int, text: str):
        state = self.state["state"]
        data = self.state.get("data") or {}
        if state.startswith("new_req:"):
            await self.handle_new_request_state(chat_id, text, state, data)
        elif state.startswith("profile:"):
            await self.handle_profile_state(chat_id, text, state, data)
        elif state.startswith("admin:"):
            await self.handle_admin_state(chat_id, text, state, data)

    async def handle_new_request_state(self, chat_id: int, text: str, state: str, data: dict):
        step = state.replace("new_req:", "")

        if step == "custom_cat":
            data["custom_category"] = text
            await self.set_state(self.user["telegram_id"], "new_req:title", data)
            await self.telegram.send_message(chat_id, lang.get("step_title_short"))

        elif step == "title":
            if len(text) < 10 or len(text) > 200:
                await self.telegram.send_message(chat_id, lang.get("title_error"))
                return
            data["title"] = text
            await self.set_state(self.user["telegram_id"], "new_req:description", data)
            await self.telegram.send_message(chat_id, lang.get("step_description"))

        elif step == "description":
            if len(text) < 30:
                await self.telegram.send_message(chat_id, lang.get("description_error"))
                return
            data["description"] = text
            await self.set_state(self.user["telegram_id"], "new_req:requirements", data)
            await self.telegram.send_message(chat_id, lang.get("step_requirements"))

        elif step == "requirements":
            data["requirements"] = None if text == "/skip" else text
            await self.set_state(self.user["telegram_id"], "new_req:compensation", data)
            keyboard = [
                [{"text": lang.get("comp_equity"), "callback_data": "new_req:comp:equity"},
                 {"text": lang.get("comp_paid"), "callback_data": "new_req:comp:paid"}],
                [{"text": lang.get("comp_negotiable"), "callback_data": "new_req:comp:negotiable"},
                 {"text": lang.get("comp_volunteer"), "callback_data": "new_req:comp:volunteer"}],
            ]
            await self.telegram.send_message_with_keyboard(chat_id, lang.get("step_compensation"), keyboard)

        elif step == "comp_details":
            data["compensation_details"] = None if text == "/skip" else text
            await self.set_state(self.user["telegram_id"], "new_req:location", data)
            keyboard = [[
                {"text": lang.get("loc_remote"), "callback_data": "new_req:loc:remote"},
                {"text": lang.get("loc_onsite"), "callback_data": "new_req:loc:onsite"},
                {"text": lang.get("loc_hybrid"), "callback_data": "new_req:loc:hybrid"},
            ]]
            await self.telegram.send_message_with_keyboard(chat_id, lang.get("step_location"), keyboard)

    async def handle_my_request_callback(self, chat_id: int, message_id: int, params: str):
        if params.startswith("close:"):
            request_id = int(params.replace("close:", ""))
            await db.update("teammate_requests", {"status": "closed"},
                            "id = ? AND user_id = ?", request_id, self.user["id"])
            await self.telegram.send_message(chat_id, lang.get("request_closed"))
            return

        request_id = int(params)
        request = await db.fetch(
            """SELECT r.*, c.name as category_name, c.icon
               FROM teammate_requests r
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.id = ? AND r.user_id = ?""",
            request_id, self.user["id"],
        )
        if not request:
            await self.telegram.send_message(chat_id, lang.get("request_not_found"))
            return

        text = f"{request['icon']} <b>{request['title']}</b>\n\n"
        text += lang.get("status_label") + " " + lang.get_status(request["status"]) + "\n"
        text += lang.get("responses_label") + f" {request['responses_count']}\n"
        text += lang.get("views_label") + f" {request['views_count']}\n\n"
        text += f"📝 {request['description']}\n"
        if request["status"] == "rejected" and request.get("rejection_reason"):
            text += "\n" + lang.get("rejection_reason") + f" {request['rejection_reason']}"

        keyboard = []
        if request["status"] == "approved":
            keyboard.append([{"text": lang.get("btn_close_request"),
                              "callback_data": f"my_req:close:{request_id}"}])
        keyboard.append([{"text": lang.get("back"), "callback_data": "menu:my_requests"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def handle_resource_callback(self, chat_id: int, message_id: int, params: str):
        category_id = int(params)
        resources = await db.fetch_all(
            "SELECT * FROM resources WHERE category_id = ? AND is_active = 1 "
            "ORDER BY is_featured DESC, created_at DESC LIMIT 10",
            category_id,
        )
        if not resources:
            await self.telegram.send_message(chat_id, lang.get("no_resources"))
            return

        for res in resources:
            text = ("⭐ " if res["is_featured"] else "") + f"<b>{res['title']}</b>\n\n"
            text += f"{res['description']}\n"
            if res.get("url"):
                keyboard = [[{"text": lang.get("btn_open_resource"), "url": res["url"]}]]
                await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)
            else:
                await self.telegram.send_message(chat_id, text)

    async def handle_profile_callback(self, chat_id: int, message_id: int, params: str):
        if params == "edit":
            keyboard = [
                [{"text": lang.get("btn_company_name"), "callback_data": "profile:set:company"}],
                [{"text": lang.get("btn_bio"), "callback_data": "profile:set:bio"}],
                [{"text": lang.get("btn_linkedin"), "callback_data": "profile:set:linkedin"}],
                [{"text": lang.get("back"), "callback_data": "menu:profile"}],
            ]
            await self.telegram.send_message_with_keyboard(chat_id, lang.get("edit_what"), keyboard)
        elif params.startswith("set:"):
            field = params.replace("set:", "")
            await self.set_state(self.user["telegram_id"], f"profile:{field}")
            prompts = {
                "company": lang.get("enter_company"),
                "bio": lang.get("enter_bio"),
                "linkedin": lang.get("enter_linkedin"),
            }
            await self.telegram.send_message(chat_id, prompts.get(field, "Qiymatni kiriting:"))

    async def handle_profile_state(self, chat_id: int, text: str, state: str, data: dict):
        field = state.replace("profile:", "")
        column_map = {"company": "company_name", "bio": "bio", "linkedin": "linkedin_url"}
        if field not in column_map:
            return
        await db.update("users", {column_map[field]: text}, "id = ?", self.user["id"])
        await self.set_state(self.user["telegram_id"], "idle")
        await self.telegram.send_message(chat_id, lang.get("profile_updated"))
        await self.cmd_profile(chat_id)

    async def handle_respond_callback(self, chat_id: int, message_id: int, params: str):
        request_id = int(params)
        request = await db.fetch(
            """SELECT r.*, u.telegram_id as owner_telegram_id, u.first_name as owner_name,
                      u.full_name as owner_full_name, u.language_code as owner_lang
               FROM teammate_requests r
               JOIN users u ON r.user_id = u.id
               WHERE r.id = ? AND r.status = 'approved'""",
            request_id,
        )
        if not request:
            await self.telegram.send_message(chat_id, lang.get("request_unavailable"))
            return

        existing = await db.fetch(
            "SELECT * FROM request_responses WHERE request_id = ? AND user_id = ?",
            request_id, self.user["id"],
        )
        if existing:
            await self.telegram.send_message(chat_id, lang.get("already_responded"))
            return

        await db.insert("request_responses", {"request_id": request_id, "user_id": self.user["id"]})
        await db.execute(
            "UPDATE teammate_requests SET responses_count = responses_count + 1 WHERE id = ?",
            request_id,
        )

        owner_lang = request.get("owner_lang") or "uz"
        lang.set_lang(owner_lang)

        responder_name = self.user.get("full_name") or self.user["first_name"]
        responder_username = f"@{self.user['username']}" if self.user.get("username") else "username yo'q"

        notify = lang.get("new_response_title")
        notify += lang.get("someone_interested", request["title"])
        notify += lang.get("from_user") + f" {responder_name} ({responder_username})\n"
        if self.user.get("profession"):
            notify += f"💼 {self.user['profession']}\n"
        if self.user.get("city"):
            notify += f"🏙 {self.user['city']}\n"
        notify += "\n" + lang.get("contact_hint")

        try:
            await self.telegram.send_message(request["owner_telegram_id"], notify)
        except TelegramError:
            pass

        lang.set_lang(self.user.get("language_code") or "uz")
        owner_name = request.get("owner_full_name") or request.get("owner_name")
        await self.telegram.send_message(chat_id, lang.get("interest_sent", owner_name))

    # ==================== HELPERS ====================

    async def get_or_create_user(self, from_: dict) -> dict:
        user = await db.fetch("SELECT * FROM users WHERE telegram_id = ?", from_["id"])
        if user:
            await db.update("users", {
                "username": from_.get("username"),
                "first_name": from_["first_name"],
                "last_name": from_.get("last_name"),
            }, "telegram_id = ?", from_["id"])
            return await db.fetch("SELECT * FROM users WHERE telegram_id = ?", from_["id"])

        new_id = await db.insert("users", {
            "telegram_id": from_["id"],
            "username": from_.get("username"),
            "first_name": from_["first_name"],
            "last_name": from_.get("last_name"),
            "language_code": "new",
            "is_registered": 0,
        })
        return await db.fetch("SELECT * FROM users WHERE id = ?", new_id)

    async def get_state(self, telegram_id: int) -> dict | None:
        # data column is jsonb -> already a dict via codec
        return await db.fetch("SELECT * FROM conversation_states WHERE telegram_id = ?", telegram_id)

    async def set_state(self, telegram_id: int, state: str, data: dict | None = None):
        await db.execute(
            """INSERT INTO conversation_states (telegram_id, state, data)
               VALUES (?, ?, ?)
               ON CONFLICT (telegram_id)
               DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data""",
            telegram_id, state, data,
        )
        self.state = {"state": state, "data": data}

    def parse_callback(self, data: str) -> tuple[str, str]:
        parts = data.split(":", 1)
        return parts[0], (parts[1] if len(parts) > 1 else "")

    # ==================== ADMIN ====================

    def is_admin(self) -> bool:
        return self.user["telegram_id"] in config.ADMIN_IDS

    async def cmd_admin(self, chat_id: int):
        if not self.is_admin():
            await self.telegram.send_message(chat_id, "⛔ Sizda admin huquqi yo'q.")
            return

        pending = await db.count("teammate_requests", "status = 'pending'")
        users = await db.count("users", "1=1")
        events = await db.count("events", "is_active = 1")
        resources = await db.count("resources", "is_active = 1")

        text = "🔐 <b>Admin Panel</b>\n\n📊 Statistika:\n"
        text += f"👥 Foydalanuvchilar: {users}\n"
        text += f"📝 Kutilayotgan e'lonlar: {pending}\n"
        text += f"🎯 Faol tadbirlar: {events}\n"
        text += f"📚 Resurslar: {resources}\n"

        keyboard = [
            [{"text": f"📝 Kutilayotgan e'lonlar ({pending})", "callback_data": "admin:pending"}],
            [{"text": f"🎯 Tadbirlar ({events})", "callback_data": "admin:events"}],
            [{"text": f"📚 Resurslar ({resources})", "callback_data": "admin:resources"}],
            [{"text": "👥 Foydalanuvchilar", "callback_data": "admin:users"}],
            [{"text": "📊 Statistika", "callback_data": "admin:stats"}],
            [{"text": "📢 Xabar yuborish", "callback_data": "admin:broadcast"}],
            [{"text": lang.get("back_to_menu"), "callback_data": "menu:main"}],
        ]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def handle_admin_callback(self, chat_id: int, message_id: int, params: str):
        if not self.is_admin():
            await self.telegram.send_message(chat_id, "⛔ Sizda admin huquqi yo'q.")
            return

        parts = params.split(":")
        action = parts[0]
        id_ = parts[1] if len(parts) > 1 else None

        if action == "pending":
            await self.show_pending_requests(chat_id)
        elif action == "view":
            await self.show_request_for_admin(chat_id, int(id_))
        elif action == "approve":
            await self.approve_request(chat_id, int(id_))
        elif action == "reject":
            await self.set_state(self.user["telegram_id"], "admin:reject", {"request_id": int(id_)})
            await self.telegram.send_message(chat_id, "📝 Rad etish sababini yozing:")
        elif action == "events":
            await self.show_admin_events(chat_id)
        elif action == "add_event":
            await self.set_state(self.user["telegram_id"], "admin:event_title")
            await self.telegram.send_message(chat_id, lang.get("admin_event_title"))
        elif action == "delete_event":
            await db.execute("UPDATE events SET is_active = 1 - is_active WHERE id = ?", int(id_))
            await self.telegram.send_message(chat_id, lang.get("admin_event_deleted"))
            await self.show_admin_events(chat_id)
        elif action == "resources":
            await self.show_admin_resources(chat_id)
        elif action == "add_resource":
            await self.show_resource_category_select(chat_id)
        elif action == "res_cat":
            await self.set_state(self.user["telegram_id"], "admin:resource_title", {"category_id": int(id_)})
            await self.telegram.send_message(chat_id, lang.get("admin_resource_title"))
        elif action == "delete_resource":
            await db.execute("UPDATE resources SET is_active = 0 WHERE id = ?", int(id_))
            await self.telegram.send_message(chat_id, lang.get("admin_resource_deleted"))
            await self.show_admin_resources(chat_id)
        elif action == "users":
            await self.show_users_for_admin(chat_id, int(id_ or 0))
        elif action == "ban":
            await self.toggle_ban_user(chat_id, int(id_))
        elif action == "stats":
            await self.show_statistics(chat_id)
        elif action == "broadcast":
            await self.set_state(self.user["telegram_id"], "admin:broadcast")
            keyboard = [[{"text": lang.get("cancel"), "callback_data": "admin:cancel"}]]
            await self.telegram.send_message_with_keyboard(
                chat_id,
                "📢 <b>Xabar yuborish</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:",
                keyboard,
            )
        elif action == "confirm_broadcast":
            await self.execute_broadcast(chat_id)
        elif action == "cancel":
            await self.set_state(self.user["telegram_id"], "idle")
            await self.cmd_admin(chat_id)
        elif action == "back":
            await self.cmd_admin(chat_id)

    async def handle_admin_state(self, chat_id: int, text: str, state: str, data: dict):
        step = state.replace("admin:", "")

        if step == "reject":
            request_id = data["request_id"]
            await db.update("teammate_requests",
                            {"status": "rejected", "rejection_reason": text}, "id = ?", request_id)
            request = await db.fetch(
                """SELECT r.*, u.telegram_id as user_tg_id, u.language_code
                   FROM teammate_requests r JOIN users u ON r.user_id = u.id WHERE r.id = ?""",
                request_id,
            )
            if request:
                lang.set_lang(request.get("language_code") or "uz")
                try:
                    await self.telegram.send_message(
                        request["user_tg_id"],
                        f"❌ <b>E'loningiz rad etildi</b>\n\n📝 {request['title']}\n\n💬 Sabab: {text}",
                    )
                except TelegramError:
                    pass
                lang.set_lang(self.user.get("language_code") or "uz")
            await self.set_state(self.user["telegram_id"], "idle")
            await self.telegram.send_message(chat_id, "✅ E'lon rad etildi.")
            await self.show_pending_requests(chat_id)

        elif step == "broadcast":
            data["message"] = text
            await self.set_state(self.user["telegram_id"], "admin:broadcast_confirm", data)
            keyboard = [
                [{"text": "✅ Yuborish", "callback_data": "admin:confirm_broadcast"}],
                [{"text": "❌ Bekor qilish", "callback_data": "admin:cancel"}],
            ]
            await self.telegram.send_message_with_keyboard(
                chat_id,
                f"📢 <b>Xabarni tasdiqlang:</b>\n\n{text}\n\n⚠️ Bu xabar barcha foydalanuvchilarga yuboriladi!",
                keyboard,
            )

        elif step == "event_title":
            title = text.strip()
            if title == "" or len(title) > 255:
                await self.telegram.send_message(chat_id, "❌ Title must be 1-255 characters. Try again:")
                return
            data["title"] = title
            await self.set_state(self.user["telegram_id"], "admin:event_description", data)
            await self.telegram.send_message(chat_id, lang.get("admin_event_description"))

        elif step == "event_description":
            desc = text.strip()
            if desc == "":
                await self.telegram.send_message(chat_id, "❌ Description cannot be empty. Try again:")
                return
            data["description"] = desc[:4000]
            await self.set_state(self.user["telegram_id"], "admin:event_image", data)
            await self.telegram.send_message(
                chat_id, lang.get("admin_event_image") + "\n\n<i>Send /skip to skip image.</i>"
            )

        elif step == "event_image":
            if text.strip() == "/skip":
                data["image_file_id"] = None
                await self.set_state(self.user["telegram_id"], "admin:event_date", data)
                await self.telegram.send_message(chat_id, lang.get("admin_event_date"))
            else:
                await self.telegram.send_message(chat_id, "❌ Please send a photo, or type /skip.")

        elif step == "event_date":
            raw = text.strip()
            dt = None
            for fmt in ("%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"):
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
            if not dt:
                await self.telegram.send_message(chat_id, lang.get("admin_event_date_error"))
                return
            if dt.timestamp() < datetime.now().timestamp():
                await self.telegram.send_message(chat_id, "❌ Event date must be in the future.")
                return
            data["event_date"] = dt
            await self.set_state(self.user["telegram_id"], "admin:event_location", data)
            await self.telegram.send_message(
                chat_id, lang.get("admin_event_location") + "\n\n<i>Send /skip to skip location.</i>"
            )

        elif step == "event_location":
            loc = text.strip()
            data["location"] = None if loc in ("", "/skip") else loc[:255]
            await self.set_state(self.user["telegram_id"], "admin:event_url", data)
            await self.telegram.send_message(chat_id, lang.get("admin_event_url"))

        elif step == "event_url":
            url = text.strip()
            if url in ("", "/skip"):
                data["registration_url"] = None
            elif not (url.startswith("http://") or url.startswith("https://")):
                await self.telegram.send_message(chat_id, "❌ Invalid URL. Send a valid link or /skip.")
                return
            else:
                data["registration_url"] = url[:500]

            try:
                await db.insert("events", {
                    "title": data.get("title", "(untitled)"),
                    "description": data.get("description", ""),
                    "image_file_id": data.get("image_file_id"),
                    "event_date": data.get("event_date") or datetime.now(),
                    "location": data.get("location"),
                    "registration_url": data.get("registration_url"),
                    "is_active": 1,
                    "created_by": self.user.get("id"),
                })
            except Exception as e:  # noqa: BLE001
                print(f"[event_create] {e}")
                await self.set_state(self.user["telegram_id"], "idle")
                await self.telegram.send_message(chat_id, f"❌ Failed to save event: {e}")
                return

            await self.set_state(self.user["telegram_id"], "idle")
            await self.telegram.send_message(chat_id, lang.get("admin_event_created", data["title"]))
            await self.show_admin_events(chat_id)

        elif step == "resource_title":
            data["title"] = text
            await self.set_state(self.user["telegram_id"], "admin:resource_description", data)
            await self.telegram.send_message(chat_id, lang.get("admin_resource_description"))

        elif step == "resource_description":
            data["description"] = text
            await self.set_state(self.user["telegram_id"], "admin:resource_url", data)
            await self.telegram.send_message(chat_id, lang.get("admin_resource_url"))

        elif step == "resource_url":
            data["url"] = None if text == "/skip" else text
            await db.insert("resources", {
                "category_id": data["category_id"],
                "title": data["title"],
                "description": data["description"],
                "url": data["url"],
                "is_active": 1,
            })
            await self.set_state(self.user["telegram_id"], "idle")
            await self.telegram.send_message(chat_id, lang.get("admin_resource_created", data["title"]))
            await self.show_admin_resources(chat_id)

    async def show_pending_requests(self, chat_id: int):
        requests = await db.fetch_all(
            """SELECT r.*, u.full_name, u.first_name, u.username, c.name as category_name, c.icon
               FROM teammate_requests r
               JOIN users u ON r.user_id = u.id
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.status = 'pending'
               ORDER BY r.created_at ASC LIMIT 20"""
        )
        if not requests:
            keyboard = [[{"text": "🔙 Orqaga", "callback_data": "admin:back"}]]
            await self.telegram.send_message_with_keyboard(chat_id, "✅ Kutilayotgan e'lonlar yo'q!", keyboard)
            return

        text = f"📝 <b>Kutilayotgan e'lonlar:</b> ({len(requests)} ta)\n\n"
        keyboard = []
        for req in requests:
            name = req.get("full_name") or req["first_name"]
            title = req["title"][:25]
            keyboard.append([{"text": f"{req['icon']} {title} - {name}",
                              "callback_data": f"admin:view:{req['id']}"}])
        keyboard.append([{"text": "🔙 Orqaga", "callback_data": "admin:back"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def show_request_for_admin(self, chat_id: int, request_id: int):
        request = await db.fetch(
            """SELECT r.*, u.full_name, u.first_name, u.username, u.profession, u.city,
                      c.name as category_name, c.icon
               FROM teammate_requests r
               JOIN users u ON r.user_id = u.id
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.id = ?""",
            request_id,
        )
        if not request:
            await self.telegram.send_message(chat_id, "E'lon topilmadi.")
            return

        name = request.get("full_name") or request["first_name"]
        username = f"@{request['username']}" if request.get("username") else "username yo'q"

        text = f"{request['icon']} <b>{request['title']}</b>\n\n"
        text += f"👤 <b>Foydalanuvchi:</b> {name} ({username})\n"
        text += f"💼 {request['profession']} | 🏙 {request['city']}\n\n"
        text += f"📁 <b>Kategoriya:</b> {request['category_name']}\n\n"
        text += f"📝 <b>Tavsif:</b>\n{request['description']}\n\n"
        if request.get("requirements"):
            text += f"✅ <b>Talablar:</b> {request['requirements']}\n\n"
        text += "💰 <b>To'lov:</b> " + lang.get_compensation_type(request["compensation_type"])
        if request.get("compensation_details"):
            text += f" - {request['compensation_details']}"
        text += "\n📍 <b>Joylashuv:</b> " + lang.get_location_type(request["location_type"])

        keyboard = [
            [{"text": "✅ Tasdiqlash", "callback_data": f"admin:approve:{request_id}"},
             {"text": "❌ Rad etish", "callback_data": f"admin:reject:{request_id}"}],
            [{"text": "🔙 Orqaga", "callback_data": "admin:pending"}],
        ]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def approve_request(self, chat_id: int, request_id: int):
        await db.update("teammate_requests", {"status": "approved"}, "id = ?", request_id)
        request = await db.fetch(
            """SELECT r.*, u.telegram_id as user_tg_id, u.language_code, u.full_name,
                      u.first_name, u.username, c.name as category_name, c.icon
               FROM teammate_requests r
               JOIN users u ON r.user_id = u.id
               JOIN teammate_categories c ON r.category_id = c.id
               WHERE r.id = ?""",
            request_id,
        )
        if request:
            lang.set_lang(request.get("language_code") or "uz")
            try:
                await self.telegram.send_message(
                    request["user_tg_id"],
                    f"✅ <b>E'loningiz tasdiqlandi!</b>\n\n📝 {request['title']}\n\n"
                    "Endi boshqalar sizning e'loningizni ko'rishi mumkin.",
                )
            except TelegramError:
                pass
            await self.post_to_channel(request, request_id)
            lang.set_lang(self.user.get("language_code") or "uz")

        await self.telegram.send_message(chat_id, "✅ E'lon tasdiqlandi!")
        await self.show_pending_requests(chat_id)

    async def post_to_channel(self, request: dict, request_id: int):
        channel = config.POSTING_CHANNEL
        bot_username = config.BOT_USERNAME or "startupper_uz_bot"
        if not channel:
            return

        poster_name = request.get("full_name") or request["first_name"]
        text = f"{request['icon']} <b>{request['title']}</b>\n\n"
        text += f"📝 {request['description']}\n\n"
        if request.get("requirements"):
            text += f"✅ <b>Talablar:</b> {request['requirements']}\n\n"
        text += "💰 <b>To'lov:</b> " + lang.get_compensation_type(request["compensation_type"])
        if request.get("compensation_details"):
            text += f" - {request['compensation_details']}"
        text += "\n📍 <b>Joylashuv:</b> " + lang.get_location_type(request["location_type"])
        text += f"\n\n👤 <b>E'lon beruvchi:</b> {poster_name}"

        keyboard = [[{"text": "📩 Murojaat qilish",
                      "url": f"https://t.me/{bot_username}?start=apply_{request_id}"}]]
        try:
            await self.telegram.send_to_channel(channel, text, keyboard)
            print(f"Channel post SUCCESS for request #{request_id} to {channel}")
        except TelegramError as e:
            print(f"Failed to post to channel {channel}: {e}")

    async def show_users_for_admin(self, chat_id: int, page: int = 0):
        limit = 10
        offset = page * limit
        users = await db.fetch_all(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", limit, offset
        )
        total_users = await db.count("users", "1=1")
        total_pages = max(1, -(-total_users // limit))  # ceil

        text = f"👥 <b>Foydalanuvchilar</b> ({total_users} ta)\n"
        text += f"📄 Sahifa: {page + 1}/{total_pages}\n\n"

        keyboard = []
        for u in users:
            name = u.get("full_name") or u["first_name"]
            status = "🚫" if u["is_banned"] else ("✅" if u["is_registered"] else "⏳")
            keyboard.append([{"text": f"{status} {name}", "callback_data": f"admin:ban:{u['id']}"}])

        nav = []
        if page > 0:
            nav.append({"text": "⬅️ Oldingi", "callback_data": f"admin:users:{page - 1}"})
        if page < total_pages - 1:
            nav.append({"text": "➡️ Keyingi", "callback_data": f"admin:users:{page + 1}"})
        if nav:
            keyboard.append(nav)
        keyboard.append([{"text": "🔙 Orqaga", "callback_data": "admin:back"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def toggle_ban_user(self, chat_id: int, user_id: int):
        user = await db.fetch("SELECT * FROM users WHERE id = ?", user_id)
        if not user:
            await self.telegram.send_message(chat_id, "Foydalanuvchi topilmadi.")
            return
        new_status = 0 if user["is_banned"] else 1
        await db.update("users", {"is_banned": new_status}, "id = ?", user_id)
        name = user.get("full_name") or user["first_name"]
        action = "🚫 bloklandi" if new_status else "✅ blokdan chiqarildi"
        await self.telegram.send_message(chat_id, f"👤 {name} {action}")
        await self.show_users_for_admin(chat_id)

    async def show_statistics(self, chat_id: int):
        total_users = await db.count("users", "1=1")
        registered = await db.count("users", "is_registered = 1")
        banned = await db.count("users", "is_banned = 1")
        total_req = await db.count("teammate_requests", "1=1")
        pending = await db.count("teammate_requests", "status = 'pending'")
        approved = await db.count("teammate_requests", "status = 'approved'")
        rejected = await db.count("teammate_requests", "status = 'rejected'")
        closed = await db.count("teammate_requests", "status = 'closed'")
        responses = await db.count("request_responses", "1=1")
        total_events = await db.count("events", "1=1")
        active_events = await db.count("events", "is_active = 1 AND event_date >= NOW()")
        total_resources = await db.count("resources", "is_active = 1")

        today = datetime.now().date()
        new_users_today = await db.count("users", "DATE(created_at) = ?", today)
        new_req_today = await db.count("teammate_requests", "DATE(created_at) = ?", today)

        text = "📊 <b>Statistika</b>\n\n"
        text += "👥 <b>Foydalanuvchilar:</b>\n"
        text += f"├ Jami: {total_users}\n├ Ro'yxatdan o'tgan: {registered}\n"
        text += f"├ Bloklangan: {banned}\n└ Bugun qo'shilgan: {new_users_today}\n\n"
        text += "📝 <b>E'lonlar:</b>\n"
        text += f"├ Jami: {total_req}\n├ 🟡 Kutilmoqda: {pending}\n├ 🟢 Tasdiqlangan: {approved}\n"
        text += f"├ 🔴 Rad etilgan: {rejected}\n├ ⚫ Yopilgan: {closed}\n└ Bugun: {new_req_today}\n\n"
        text += f"🎯 <b>Tadbirlar:</b>\n├ Jami: {total_events}\n└ Faol: {active_events}\n\n"
        text += f"📚 <b>Resurslar:</b> {total_resources}\n\n"
        text += f"💬 <b>Javoblar:</b> {responses}"

        keyboard = [[{"text": "🔙 Orqaga", "callback_data": "admin:back"}]]
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def execute_broadcast(self, chat_id: int):
        import asyncio

        self.state = await self.get_state(self.user["telegram_id"])
        message = (self.state.get("data") or {}).get("message")
        if not message:
            await self.telegram.send_message(chat_id, "⚠️ Xabar topilmadi.")
            await self.cmd_admin(chat_id)
            return

        users = await db.fetch_all("SELECT telegram_id FROM users WHERE is_banned = 0")
        sent = failed = 0
        await self.telegram.send_message(
            chat_id, f"📤 Xabar yuborilmoqda... ({len(users)} ta foydalanuvchi)"
        )
        for u in users:
            try:
                await self.telegram.send_message(u["telegram_id"], message)
                sent += 1
                await asyncio.sleep(0.05)
            except TelegramError:
                failed += 1

        await self.set_state(self.user["telegram_id"], "idle")
        await self.telegram.send_message(
            chat_id, f"✅ <b>Xabar yuborildi!</b>\n\n📤 Yuborildi: {sent}\n❌ Xato: {failed}"
        )
        await self.cmd_admin(chat_id)

    async def show_admin_events(self, chat_id: int):
        events = await db.fetch_all("SELECT * FROM events ORDER BY event_date DESC LIMIT 20")
        text = lang.get("admin_events_list") + "\n\n"
        if not events:
            text += "📭 Hozircha tadbirlar yo'q."
        keyboard = [[{"text": "➕ Tadbir qo'shish", "callback_data": "admin:add_event"}]]
        for event in events:
            date = event["event_date"]
            date_str = date.strftime("%d.%m.%Y") if isinstance(date, datetime) else str(date)
            status = "✅" if event["is_active"] else "❌"
            title = event["title"][:25]
            keyboard.append([{"text": f"{status} {date_str} - {title}",
                              "callback_data": f"admin:delete_event:{event['id']}"}])
        keyboard.append([{"text": "🔙 Orqaga", "callback_data": "admin:back"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def handle_event_photo(self, chat_id: int, photos: list):
        if not self.is_admin():
            return
        photo = photos[-1]  # largest
        file_id = photo["file_id"]
        self.state = await self.get_state(self.user["telegram_id"])
        data = (self.state or {}).get("data") or {}
        data["image_file_id"] = file_id
        await self.set_state(self.user["telegram_id"], "admin:event_date", data)
        await self.telegram.send_message(chat_id, lang.get("admin_event_date"))

    async def show_admin_resources(self, chat_id: int):
        resources = await db.fetch_all(
            """SELECT r.*, rc.name as category_name, rc.icon
               FROM resources r
               JOIN resource_categories rc ON r.category_id = rc.id
               WHERE r.is_active = 1
               ORDER BY r.created_at DESC LIMIT 20"""
        )
        text = lang.get("admin_resources_list") + "\n\n"
        if not resources:
            text += "📭 Hozircha resurslar yo'q."
        keyboard = [[{"text": "➕ Resurs qo'shish", "callback_data": "admin:add_resource"}]]
        for res in resources:
            title = res["title"][:25]
            keyboard.append([{"text": f"{res['icon']} {title}",
                              "callback_data": f"admin:delete_resource:{res['id']}"}])
        keyboard.append([{"text": "🔙 Orqaga", "callback_data": "admin:back"}])
        await self.telegram.send_message_with_keyboard(chat_id, text, keyboard)

    async def show_resource_category_select(self, chat_id: int):
        categories = await db.fetch_all(
            "SELECT * FROM resource_categories WHERE is_active = 1 ORDER BY sort_order"
        )
        if not categories:
            await self.telegram.send_message(chat_id, "⚠️ Avval kategoriyalar qo'shing (web admin paneldan).")
            await self.show_admin_resources(chat_id)
            return
        keyboard = []
        for cat in categories:
            keyboard.append([{"text": f"{cat['icon']} {cat['name']}",
                              "callback_data": f"admin:res_cat:{cat['id']}"}])
        keyboard.append([{"text": lang.get("cancel"), "callback_data": "admin:resources"}])
        await self.telegram.send_message_with_keyboard(chat_id, lang.get("admin_resource_category"), keyboard)

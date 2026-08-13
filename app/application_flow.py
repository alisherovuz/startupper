"""
Registration flow — repurposed for "Startap Mafiaga ro'yxatdan o'tish"
"""
import html
from datetime import datetime
from io import BytesIO

from . import config, db
from .telegram import Telegram, TelegramError

def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)

async def _get_state(uid: int):
    return await db.fetch("SELECT * FROM conversation_states WHERE telegram_id = ?", uid)

async def _set_state(uid: int, state: str, data: dict | None = None):
    await db.execute(
        """INSERT INTO conversation_states (telegram_id, state, data)
           VALUES (?, ?, ?)
           ON CONFLICT (telegram_id)
           DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data""",
        uid, state, data,
    )

async def _clear_state(uid: int):
    await _set_state(uid, "idle", None)


class ApplicationFlow:
    def __init__(self, telegram: Telegram):
        self.tg = telegram

    async def maybe_handle(self, update: dict) -> bool:
        if "callback_query" in update:
            cb = update["callback_query"]
            data = cb.get("data", "")
            if data == "mafia:start":
                await self.tg.answer_callback(cb["id"])
                await self._start_mafia(cb["message"]["chat"]["id"], cb["from"])
                return True
            if data.startswith("admin:mafia_approve:"):
                await self.tg.answer_callback(cb["id"])
                await self._handle_admin_decision(cb["message"]["chat"]["id"], data)
                return True
            if data.startswith("admin:mafia_reject:"):
                await self.tg.answer_callback(cb["id"])
                await self._handle_admin_decision(cb["message"]["chat"]["id"], data)
                return True
            return False

        if "message" not in update:
            return False

        msg = update["message"]
        from_ = msg.get("from", {})
        uid = from_.get("id")
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "") or ""
        cmd = text.split()[0].split("@")[0] if text.startswith("/") else ""

        if cmd == "/export":
            await self._handle_export(chat_id, from_)
            return True
        if cmd == "/mafia":
            await self._start_mafia(chat_id, from_)
            return True

        st = await _get_state(uid)
        if st and st["state"].startswith("mafia:"):
            if cmd == "/cancel":
                await _clear_state(uid)
                await self.tg.remove_keyboard(chat_id, "❌ Bekor qilindi.")
                return True
            if cmd:
                await _clear_state(uid)
                return False
            await self._handle_answer(chat_id, from_, st, msg)
            return True

        return False

    async def _start_mafia(self, chat_id: int, from_: dict):
        uid = from_["id"]
        
        # Check if already registered (Disabled temporarily for testing)
        # existing = await db.fetch("SELECT id, status FROM mafia_registrations WHERE telegram_id = ? ORDER BY id DESC", uid)
        # if existing:
        #     await self.tg.send_message(
        #         chat_id, 
        #         f"Siz allaqachon ariza topshirgansiz. Arizangiz holati: {existing['status']}."
        #     )
        #     return

        await _set_state(uid, "mafia:name", {})
        text = "📝 <b>Startap Mafiaga ro'yxatdan o'tish</b>\n\nIltimos, ism-familiyangizni kiriting:"
        await self.tg.send_message(chat_id, text)

    async def _handle_answer(self, chat_id: int, from_: dict, st: dict, msg: dict):
        uid = from_["id"]
        state = st["state"]
        data = st.get("data") or {}

        text = msg.get("text", "") or ""
        contact = msg.get("contact")
        photo = msg.get("photo")

        if state == "mafia:name":
            if not text.strip():
                await self.tg.send_message(chat_id, "Iltimos, ismingizni matn ko'rinishida yuboring.")
                return
            data["full_name"] = text
            await _set_state(uid, "mafia:phone", data)
            keyboard = [[{"text": "📱 Telefon raqamni yuborish", "request_contact": True}]]
            await self.tg.send_message_with_keyboard(
                chat_id, 
                "Telefon raqamingizni pastdagi tugma orqali yuboring yoki yozing:", 
                keyboard, 
                inline=False
            )

        elif state == "mafia:phone":
            phone = contact.get("phone_number") if contact else text.strip()
            if not phone:
                await self.tg.send_message(chat_id, "Iltimos, telefon raqamingizni yuboring.")
                return
            data["phone"] = phone
            await _set_state(uid, "mafia:receipt", data)
            
            qr_url = "zoomrad_qr.png"
            
            amount = "50 000 so'm"
            
            text_receipt = (
                f"🟣 <b>To'lov:</b> Zoomrad orqali\n"
                f"💰 <b>Summa:</b> {amount}\n\n"
                f"QR kod orqali to'lab, chekni (screenshot) yuboring."
            )
            await self.tg.send_photo(
                chat_id, 
                qr_url, 
                caption=text_receipt, 
                reply_markup={"remove_keyboard": True}
            )
        elif state == "mafia:receipt":
            if not photo:
                await self.tg.send_message(chat_id, "Iltimos, to'lov chekini rasm (screenshot) ko'rinishida yuboring.")
                return
            
            largest_photo = photo[-1]
            file_id = largest_photo["file_id"]
            data["receipt"] = file_id
            
            await self._finish_mafia(chat_id, from_, data)
            await _clear_state(uid)

    async def _finish_mafia(self, chat_id: int, from_: dict, data: dict):
        uid = from_["id"]
        username = from_.get("username")

        try:
            reg_id = await db.insert("mafia_registrations", {
                "telegram_id": uid,
                "username": username,
                "full_name": data.get("full_name"),
                "phone_number": data.get("phone"),
                "receipt_file_id": data.get("receipt"),
                "status": "pending",
            })
            
            # Notify admin
            uname_disp = f"@{username}" if username else "—"
            report = (
                "🆕 <b>Startap Mafia: Yangi to'lov</b>\n\n"
                f"👤 <b>Ism:</b> {esc(data.get('full_name'))}\n"
                f"📱 <b>Telefon:</b> {esc(data.get('phone'))}\n"
                f"🔗 <b>Username:</b> {uname_disp} (ID: <code>{uid}</code>)"
            )
            keyboard = [
                [{"text": "✅ Tasdiqlash", "callback_data": f"admin:mafia_approve:{reg_id}"}],
                [{"text": "❌ Rad etish", "callback_data": f"admin:mafia_reject:{reg_id}"}]
            ]
            
            target = config.TARGET_CHAT_ID or config.ADMIN_ID
            if target:
                await self.tg.send_photo_with_keyboard(target, data["receipt"], report, keyboard)

        except Exception as e:
            print(f"[mafia save] {e}")

        await self.tg.send_message(
            chat_id,
            "✅ <b>Arizangiz qabul qilindi!</b>\n\nTo'lov ma'muriyat tomonidan tekshirilgandan so'ng sizga xabar beramiz."
        )

    async def _handle_admin_decision(self, chat_id: int, callback_data: str):
        parts = callback_data.split(":")
        action = parts[1] # mafia_approve or mafia_reject
        reg_id = int(parts[2])

        row = await db.fetch("SELECT * FROM mafia_registrations WHERE id = ?", reg_id)
        if not row:
            await self.tg.send_message(chat_id, "⚠️ Bu ariza topilmadi.")
            return

        if row["status"] != "pending":
            await self.tg.send_message(chat_id, f"⚠️ Bu ariza allaqachon {row['status']} qilingan.")
            return

        new_status = "approved" if action == "mafia_approve" else "rejected"
        await db.update("mafia_registrations", {"status": new_status}, "id = ?", reg_id)

        try:
            if new_status == "approved":
                await self.tg.send_message(
                    row["telegram_id"], 
                    "🎉 <b>Tabriklaymiz!</b>\n\nTo'lovingiz tasdiqlandi va siz Startap Mafiaga qabul qilindingiz!"
                )
            else:
                await self.tg.send_message(
                    row["telegram_id"], 
                    "❌ Afsuski, sizning to'lovingiz tasdiqlanmadi. Iltimos, ma'muriyat bilan bog'laning."
                )
        except TelegramError:
            pass

        msg = "✅ Tasdiqlandi" if new_status == "approved" else "❌ Rad etildi"
        await self.tg.send_message(chat_id, f"Ariza #{reg_id}: {msg}")

    async def _handle_export(self, chat_id: int, from_: dict):
        uid = from_["id"]
        if uid not in config.ADMIN_IDS:
            await self.tg.send_message(chat_id, "⛔ Bu buyruq faqat admin uchun.")
            return

        rows = await db.fetch_all(
            """SELECT id, telegram_id, username, full_name, phone_number, status, created_at
               FROM mafia_registrations 
               WHERE status = 'approved'
               ORDER BY created_at DESC"""
        )

        if not rows:
            await self.tg.send_message(chat_id, "📭 Hozircha tasdiqlangan qatnashchilar yo'q.")
            return

        try:
            from openpyxl import Workbook
        except ImportError:
            await self.tg.send_message(chat_id, "⚠️ openpyxl o'rnatilmagan.")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Mafia Registrations"
        ws.append([
            "ID", "Telegram ID", "Username", "Ism-familiya", "Telefon", "Holat", "Sana"
        ])
        for r in rows:
            created = r["created_at"]
            created_str = created.strftime("%Y-%m-%d %H:%M") if isinstance(created, datetime) else str(created)
            ws.append([
                r["id"], r["telegram_id"], r["username"] or "",
                r["full_name"] or "", r["phone_number"] or "", r["status"],
                created_str,
            ])

        buf = BytesIO()
        wb.save(buf)
        content = buf.getvalue()

        filename = f"mafia_approved_{datetime.now():%Y%m%d_%H%M}.xlsx"
        try:
            await self.tg.send_document(chat_id, content, filename, caption=f"📊 Tasdiqlanganlar: {len(rows)} ta")
        except TelegramError as e:
            await self.tg.send_message(chat_id, f"⚠️ Faylni yuborib bo'lmadi: {e}")

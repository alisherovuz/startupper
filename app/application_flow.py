"""
Registration / application flow — a self-contained feature bolted onto the
existing bot (no python-telegram-bot; reuses the project's Telegram wrapper,
Postgres layer and conversation_states table).

Triggers:
  /apply (or /register)  -> 6-question application, gated behind APPLY_CHANNEL
  /export                -> admin-only .xlsx export of all applications

main.py routes every update through ApplicationFlow.maybe_handle() first; it
returns True when it has handled the update, otherwise the normal BotHandler runs.
"""
import html
from datetime import datetime
from io import BytesIO

from . import config, db
from .telegram import Telegram, TelegramError

# ---- Question prompts (Uzbek, exact order) ----
INTRO = "📝 <b>Ariza topshirish</b>\n\nQuyidagi 6 ta savolga javob bering."

Q1 = "1️⃣ <b>Jamoa nomi va a'zolar soni</b> (1–3 kishi)."
Q2 = "2️⃣ <b>Loyiha/G'oya nomi</b> va uning 1 ta gapdagi qisqacha mazmuni."
Q3 = "3️⃣ Siz yechmoqchi bo'lgan <b>muammo nima</b> va u kimlarda uchraydi? (Maqsadli auditoriya)."
Q4 = "4️⃣ <b>Nega aynan siz</b> bu muammoni yecha olasiz? (Jamoaning texnik yoki amaliy ko'nikmalari)."
Q5 = "5️⃣ <b>Trello</b> platformasi bilan ishlash tajribangiz bormi?"
Q6 = "6️⃣ Dastur uchun haftasiga kamida <b>10-15 soat</b> vaqt ajratishga qat'iy tayyormisiz?"

# ---- Reply-keyboard button texts (also used for matching answers) ----
Q5_YES = "Ha, oldin ishlaganman"
Q5_NO = "Yo'q, lekin tezda o'rganib olaman"
Q6_YES = "Ha, to'liq tayyorman!"
Q6_NO = "Yo'q, vaqtim kamroq"

Q5_KEYBOARD = [[{"text": Q5_YES}], [{"text": Q5_NO}]]
Q6_KEYBOARD = [[{"text": Q6_YES}], [{"text": Q6_NO}]]

REJECT_MSG = (
    "Rahmat! 🙏 Afsuski, bu dastur haftasiga kamida 10-15 soat vaqt talab qiladi. "
    "Hozircha arizangizni qabul qila olmaymiz, ammo keyingi imkoniyatlarda kutib qolamiz!"
)


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


# ---- state helpers (shared conversation_states table, "app:" namespace) ----

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

    # ============ entry point used by main.py ============

    async def maybe_handle(self, update: dict) -> bool:
        # Inline "I subscribed" recheck button
        if "callback_query" in update:
            cb = update["callback_query"]
            data = cb.get("data", "")
            if data == "app:checksub":
                await self._handle_checksub(cb)
                return True
            if data == "app:start":
                await self.tg.answer_callback(cb["id"])
                await self._start(cb["message"]["chat"]["id"], cb["from"])
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
        if cmd in ("/apply", "/register"):
            await self._start(chat_id, from_)
            return True

        # Mid-application?
        st = await _get_state(uid)
        if st and st["state"].startswith("app:"):
            if cmd == "/cancel":
                await _clear_state(uid)
                await self.tg.remove_keyboard(chat_id, "❌ Ariza bekor qilindi.")
                return True
            if cmd:  # any other command aborts the application; let the main bot handle it
                await _clear_state(uid)
                return False
            await self._handle_answer(chat_id, from_, st, text)
            return True

        return False

    # ============ subscription gate ============

    async def _is_subscribed(self, uid: int) -> bool:
        if not config.APPLY_CHANNEL:
            return True
        try:
            status = await self.tg.get_chat_member(config.APPLY_CHANNEL, uid)
            return status in ("member", "administrator", "creator")
        except TelegramError:
            # Bot can't read membership (e.g. not admin of the channel) -> treat as not subscribed
            return False

    async def _subscribe_prompt(self, chat_id: int):
        uname = config.APPLY_CHANNEL.lstrip("@")
        text = (
            f"📢 Avval <b>{esc(config.APPLY_CHANNEL)}</b> kanaliga obuna bo'ling, "
            "so'ng \"✅ Tekshirish\" tugmasini bosing."
        )
        keyboard = [
            [{"text": "📢 Kanalga obuna bo'lish", "url": f"https://t.me/{uname}"}],
            [{"text": "✅ Tekshirish", "callback_data": "app:checksub"}],
        ]
        await self.tg.send_message_with_keyboard(chat_id, text, keyboard)

    async def _handle_checksub(self, cb: dict):
        uid = cb["from"]["id"]
        chat_id = cb["message"]["chat"]["id"]
        if await self._is_subscribed(uid):
            await self.tg.answer_callback(cb["id"])
            await self._begin_questions(chat_id, uid)
        else:
            await self.tg.answer_callback(
                cb["id"], "Hali obuna bo'lmagansiz. Obuna bo'lib, qayta tekshiring.", show_alert=True
            )

    # ============ flow ============

    async def _start(self, chat_id: int, from_: dict):
        uid = from_["id"]
        if not await self._is_subscribed(uid):
            await self._subscribe_prompt(chat_id)
            return
        await self._begin_questions(chat_id, uid)

    async def _begin_questions(self, chat_id: int, uid: int):
        await _set_state(uid, "app:q1", {})
        await self.tg.send_message(chat_id, INTRO + "\n\n" + Q1)

    async def _handle_answer(self, chat_id: int, from_: dict, st: dict, text: str):
        uid = from_["id"]
        state = st["state"]
        data = st.get("data") or {}

        if not text.strip():
            await self.tg.send_message(chat_id, "Iltimos, javobni matn ko'rinishida yuboring.")
            return

        if state == "app:q1":
            data["q1"] = text
            await _set_state(uid, "app:q2", data)
            await self.tg.send_message(chat_id, Q2)

        elif state == "app:q2":
            data["q2"] = text
            await _set_state(uid, "app:q3", data)
            await self.tg.send_message(chat_id, Q3)

        elif state == "app:q3":
            data["q3"] = text
            await _set_state(uid, "app:q4", data)
            await self.tg.send_message(chat_id, Q4)

        elif state == "app:q4":
            data["q4"] = text
            await _set_state(uid, "app:q5", data)
            await self.tg.send_message_with_keyboard(chat_id, Q5, Q5_KEYBOARD, inline=False)

        elif state == "app:q5":
            data["q5"] = text
            await _set_state(uid, "app:q6", data)
            await self.tg.send_message_with_keyboard(chat_id, Q6, Q6_KEYBOARD, inline=False)

        elif state == "app:q6":
            # Reject if not fully committed.
            if text == Q6_NO or "kamroq" in text.lower():
                await _clear_state(uid)
                await self.tg.remove_keyboard(chat_id, REJECT_MSG)
                return
            if text != Q6_YES and "tayyorman" not in text.lower():
                # Unrecognized answer -> re-ask with the buttons.
                await self.tg.send_message_with_keyboard(chat_id, Q6, Q6_KEYBOARD, inline=False)
                return
            data["q6"] = text
            await self._finish(chat_id, from_, data)
            await _clear_state(uid)

    async def _finish(self, chat_id: int, from_: dict, data: dict):
        uid = from_["id"]
        username = from_.get("username")

        # 1) Save to Postgres
        try:
            await db.insert("applications", {
                "telegram_id": uid,
                "username": username,
                "q1_team": data.get("q1"),
                "q2_project": data.get("q2"),
                "q3_problem": data.get("q3"),
                "q4_why_you": data.get("q4"),
                "q5_trello": data.get("q5"),
                "q6_commitment": data.get("q6"),
            })
        except Exception as e:  # noqa: BLE001
            print(f"[application save] {e}")

        # 2) Send formatted report to TARGET_CHAT_ID (fallback to ADMIN_ID)
        uname_disp = f"@{username}" if username else "—"
        report = (
            "🆕 <b>Yangi ariza</b>\n\n"
            f"👤 Foydalanuvchi: {uname_disp} (ID: <code>{uid}</code>)\n\n"
            f"1️⃣ <b>Jamoa va a'zolar:</b>\n{esc(data.get('q1'))}\n\n"
            f"2️⃣ <b>Loyiha/G'oya:</b>\n{esc(data.get('q2'))}\n\n"
            f"3️⃣ <b>Muammo va auditoriya:</b>\n{esc(data.get('q3'))}\n\n"
            f"4️⃣ <b>Nega aynan ular:</b>\n{esc(data.get('q4'))}\n\n"
            f"5️⃣ <b>Trello tajribasi:</b>\n{esc(data.get('q5'))}\n\n"
            f"6️⃣ <b>Vaqt majburiyati:</b>\n{esc(data.get('q6'))}"
        )
        target = config.TARGET_CHAT_ID or config.ADMIN_ID
        if target:
            try:
                await self.tg.send_message(target, report)
            except TelegramError as e:
                print(f"[application report] {e}")

        # 3) Confirm to the applicant
        await self.tg.remove_keyboard(
            chat_id,
            "✅ <b>Arizangiz qabul qilindi!</b>\n\nTez orada siz bilan bog'lanamiz. Omad! 🚀",
        )

    # ============ /export ============

    async def _handle_export(self, chat_id: int, from_: dict):
        uid = from_["id"]
        if uid not in config.ADMIN_IDS:
            await self.tg.send_message(chat_id, "⛔ Bu buyruq faqat admin uchun.")
            return

        rows = await db.fetch_all(
            """SELECT id, telegram_id, username, q1_team, q2_project, q3_problem,
                      q4_why_you, q5_trello, q6_commitment, created_at
               FROM applications ORDER BY created_at DESC"""
        )

        if not rows:
            await self.tg.send_message(chat_id, "📭 Hozircha arizalar yo'q.")
            return

        try:
            from openpyxl import Workbook
        except ImportError:
            await self.tg.send_message(chat_id, "⚠️ openpyxl o'rnatilmagan (requirements.txt ni tekshiring).")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Applications"
        ws.append([
            "ID", "Telegram ID", "Username",
            "Jamoa (Q1)", "Loyiha (Q2)", "Muammo (Q3)",
            "Nega siz (Q4)", "Trello (Q5)", "Vaqt (Q6)", "Sana",
        ])
        for r in rows:
            created = r["created_at"]
            created_str = created.strftime("%Y-%m-%d %H:%M") if isinstance(created, datetime) else str(created)
            ws.append([
                r["id"], r["telegram_id"], r["username"] or "",
                r["q1_team"] or "", r["q2_project"] or "", r["q3_problem"] or "",
                r["q4_why_you"] or "", r["q5_trello"] or "", r["q6_commitment"] or "",
                created_str,
            ])

        buf = BytesIO()
        wb.save(buf)
        content = buf.getvalue()

        filename = f"applications_{datetime.now():%Y%m%d_%H%M}.xlsx"
        try:
            await self.tg.send_document(chat_id, content, filename, caption=f"📊 Arizalar: {len(rows)} ta")
        except TelegramError as e:
            await self.tg.send_message(chat_id, f"⚠️ Faylni yuborib bo'lmadi: {e}")

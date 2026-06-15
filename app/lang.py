"""
Bilingual strings (replaces src/Core/Lang.php).

Usage:
    lang.set_lang("uz")
    lang.get("welcome_title", name)        # %s-style formatting via *args
"""

_current = {"lang": "uz"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ---------- GENERAL ----------
    "welcome_title": {"en": "Hey %s! 👋", "uz": "Salom %s! 👋"},
    "welcome_message": {
        "en": "Welcome to StartupperUZ! 🚀\n\nConnect with fellow founders, find teammates, and access resources to grow your startup.",
        "uz": "StartupperUZ ga xush kelibsiz! 🚀\n\nBoshqa tadbirkorlar bilan bog'laning, jamoa a'zolarini toping va startapingizni rivojlantirish uchun resurslardan foydalaning.",
    },
    "what_to_do": {"en": "<b>What would you like to do?</b>", "uz": "<b>Nima qilishni xohlaysiz?</b>"},
    "back_to_menu": {"en": "🔙 Back to Menu", "uz": "🔙 Menyuga qaytish"},
    "back": {"en": "🔙 Back", "uz": "🔙 Orqaga"},
    "cancel": {"en": "❌ Cancel", "uz": "❌ Bekor qilish"},
    "action_cancelled": {"en": "✅ Action cancelled.", "uz": "✅ Amal bekor qilindi."},
    "unknown_command": {
        "en": "Unknown command. Use /help to see available commands.",
        "uz": "Noma'lum buyruq. /help ni bosing.",
    },
    # ---------- SUBSCRIPTION ----------
    "subscription_required": {
        "en": "📢 <b>Join our channels first!</b>\n\nTo use the bot, please subscribe to our channels below and click \"I subscribed\".",
        "uz": "📢 <b>Avval kanallarimizga obuna bo'ling!</b>\n\nBotdan foydalanish uchun quyidagi kanallarga obuna bo'ling va \"Obuna bo'ldim\" tugmasini bosing.",
    },
    "btn_join_channel": {"en": "📢 Join Channel", "uz": "📢 Kanalga qo'shilish"},
    "btn_check_subscription": {"en": "✅ I subscribed", "uz": "✅ Obuna bo'ldim"},
    "not_subscribed": {
        "en": "❌ You're not subscribed to all channels yet. Please join all channels first.",
        "uz": "❌ Siz hali barcha kanallarga obuna bo'lmagansiz. Avval barcha kanallarga qo'shiling.",
    },
    # ---------- REGISTRATION ----------
    "registration_welcome": {
        "en": "📝 <b>Quick Registration</b>\n\nLet's get to know you better! Please answer a few questions.",
        "uz": "📝 <b>Tez ro'yxatdan o'tish</b>\n\nKeling, tanishamiz! Bir nechta savolga javob bering.",
    },
    "reg_ask_full_name": {
        "en": "👤 What is your full name?\n\n<i>Example: Alisher Karimov</i>",
        "uz": "👤 Ism-familiyangizni kiriting:\n\n<i>Masalan: Alisher Karimov</i>",
    },
    "reg_name_error": {
        "en": "⚠️ Please enter a valid name (3-100 characters).",
        "uz": "⚠️ Iltimos, to'g'ri ism kiriting (3-100 ta belgi).",
    },
    "reg_ask_age": {
        "en": "📅 How old are you?\n\n<i>Enter a number, e.g. 25</i>",
        "uz": "📅 Yoshingiz nechida?\n\n<i>Raqam kiriting, masalan: 25</i>",
    },
    "reg_age_error": {"en": "⚠️ Please enter a valid age (14-80).", "uz": "⚠️ Iltimos, to'g'ri yosh kiriting (14-80)."},
    "reg_ask_city": {"en": "🏙 Which city are you from?", "uz": "🏙 Qaysi shahardansiz?"},
    "reg_type_city": {"en": "Please type your city name:", "uz": "Shahar nomini yozing:"},
    "reg_ask_profession": {
        "en": "💼 What is your profession/role?\n\n<i>Example: Developer, Designer, Entrepreneur, Student</i>",
        "uz": "💼 Kasbingiz/lavozimingiz nima?\n\n<i>Masalan: Dasturchi, Dizayner, Tadbirkor, Talaba</i>",
    },
    "reg_success": {
        "en": "🎉 <b>Registration complete!</b>\n\nWelcome to StartupperUZ! Now you can use all features.",
        "uz": "🎉 <b>Ro'yxatdan o'tish tugadi!</b>\n\nStartupperUZ ga xush kelibsiz! Endi barcha imkoniyatlardan foydalanishingiz mumkin.",
    },
    # ---------- LANGUAGE ----------
    "choose_language": {"en": "🌐 <b>Choose your language</b>", "uz": "🌐 <b>Tilni tanlang</b>"},
    "language_set": {"en": "✅ Language set to English!", "uz": "✅ Til o'zbek tiliga o'zgartirildi!"},
    # ---------- MAIN MENU BUTTONS ----------
    "btn_find_teammate": {"en": "🔍 Find Teammate", "uz": "🔍 Jamoa topish"},
    "btn_post_request": {"en": "📝 Post Request", "uz": "📝 E'lon joylash"},
    "btn_resources": {"en": "📚 Resources", "uz": "📚 Resurslar"},
    "btn_my_profile": {"en": "👤 My Profile", "uz": "👤 Profilim"},
    "btn_my_requests": {"en": "📋 My Requests", "uz": "📋 E'lonlarim"},
    "btn_change_language": {"en": "🌐 Language", "uz": "🌐 Til"},
    # ---------- HELP ----------
    "help_title": {"en": "📖 <b>Commands</b>\n\n", "uz": "📖 <b>Buyruqlar</b>\n\n"},
    "help_commands": {
        "en": "/start - Main menu\n/find - Browse requests\n/post - Post a request\n/my_requests - Your requests\n/resources - Resources\n/profile - Your profile\n/language - Change language\n/cancel - Cancel action",
        "uz": "/start - Asosiy menyu\n/find - E'lonlarni ko'rish\n/post - E'lon joylash\n/my_requests - E'lonlaringiz\n/resources - Resurslar\n/profile - Profilingiz\n/language - Tilni o'zgartirish\n/cancel - Bekor qilish",
    },
    # ---------- FIND TEAMMATE ----------
    "find_title": {
        "en": "🔍 <b>Find a Teammate</b>\n\nSelect a category:",
        "uz": "🔍 <b>Jamoa a'zosini topish</b>\n\nKategoriyani tanlang:",
    },
    "no_requests_in_category": {
        "en": "No open requests in this category yet.",
        "uz": "Bu kategoriyada hali e'lonlar yo'q.",
    },
    "no_requests_available": {
        "en": "📭 No requests available at the moment.\n\nBe the first to post one! Use /post",
        "uz": "📭 Hozircha e'lonlar yo'q.\n\nBirinchi bo'lib e'lon joylashtiring! /post buyrug'ini bosing",
    },
    "posted_by": {"en": "👤 Posted by:", "uz": "👤 E'lon beruvchi:"},
    "requirements": {"en": "✅ Requirements:", "uz": "✅ Talablar:"},
    "compensation": {"en": "💰 Compensation:", "uz": "💰 To'lov:"},
    "location": {"en": "📍 Location:", "uz": "📍 Joylashuv:"},
    "btn_interested": {"en": "💬 I'm Interested", "uz": "💬 Qiziqaman"},
    # ---------- POST REQUEST ----------
    "post_title": {
        "en": "📝 <b>Post a Request</b>\n\nWhat type of teammate?",
        "uz": "📝 <b>E'lon joylash</b>\n\nQanday jamoa a'zosi kerak?",
    },
    "max_requests_reached": {
        "en": "⚠️ You have %d active requests. Close one to post new.",
        "uz": "⚠️ Sizda %d ta faol e'lon bor. Yangi joylash uchun birini yoping.",
    },
    "other_category_prompt": {
        "en": "📝 Please type the role you're looking for:",
        "uz": "📝 Qidirayotgan rolni yozing:",
    },
    "step_title": {
        "en": "Looking for <b>%s</b>.\n\n📌 <b>Step 1/5:</b> Enter a short title:\n\n<i>Example: \"Mobile app UI/UX designer needed\" or \"Co-founder for EdTech startup\"</i>",
        "uz": "<b>%s</b> qidiryapsiz.\n\n📌 <b>1/5-qadam:</b> E'loningiz uchun qisqa sarlavha kiriting:\n\n<i>Masalan: \"Mobil ilova uchun UI/UX dizayner kerak\" yoki \"EdTech startap uchun hamkor\"</i>",
    },
    "step_title_short": {
        "en": "📌 <b>Step 1/5:</b> Enter a short title:\n\n<i>Example: \"Mobile app UI/UX designer needed\"</i>",
        "uz": "📌 <b>1/5-qadam:</b> E'loningiz uchun qisqa sarlavha kiriting:\n\n<i>Masalan: \"Mobil ilova uchun dizayner kerak\"</i>",
    },
    "step_description": {
        "en": "📌 <b>Step 2/5:</b> Describe your project and what you need:\n\n<i>Example: \"We're building a food delivery app. Looking for a designer to create the mobile UI. The app has 15 screens. Timeline: 2 weeks.\"</i>",
        "uz": "📌 <b>2/5-qadam:</b> Loyihangiz va nimaga ehtiyojingiz borligini yozing:\n\n<i>Masalan: \"Ovqat yetkazib berish ilovasi qilyapmiz. Mobil ilova dizayni uchun dizayner kerak. 15 ta ekran bor. Muddat: 2 hafta.\"</i>",
    },
    "step_requirements": {
        "en": "📌 <b>Step 3/5:</b> What skills or experience needed?\n\n<i>Example: \"Figma experience, 2+ years mobile design\"</i>\n\nSend /skip to skip.",
        "uz": "📌 <b>3/5-qadam:</b> Qanday ko'nikma yoki tajriba kerak?\n\n<i>Masalan: \"Figma bilan ishlash, 2+ yil mobil dizayn tajribasi\"</i>\n\nO'tkazish: /skip",
    },
    "step_compensation": {
        "en": "📌 <b>Step 4/5:</b> How will you pay the teammate?",
        "uz": "📌 <b>4/5-qadam:</b> Jamoa a'zosiga qanday to'lov taklif qilasiz?",
    },
    "step_compensation_details": {
        "en": "💰 Selected: <b>%s</b>\n\nAdd details (amount, %%, etc):\n\n<i>Example: \"500 USD\" or \"10%% equity\" or \"20 USD/hour\"</i>\n\nSend /skip to skip.",
        "uz": "💰 Tanlandi: <b>%s</b>\n\nQo'shimcha ma'lumot (summa, %% va h.k.):\n\n<i>Masalan: \"500 USD\" yoki \"10%% ulush\" yoki \"soatiga 20 USD\"</i>\n\nO'tkazish: /skip",
    },
    "step_location": {
        "en": "📌 <b>Step 5/5:</b> Where will the work be done?",
        "uz": "📌 <b>5/5-qadam:</b> Ish qayerda bajariladi?",
    },
    "title_error": {"en": "⚠️ Title: 10-200 characters.", "uz": "⚠️ Sarlavha: 10-200 ta belgi."},
    "description_error": {
        "en": "⚠️ Please write more (min 30 characters).",
        "uz": "⚠️ Batafsilroq yozing (kamida 30 ta belgi).",
    },
    "request_submitted": {
        "en": "🎉 <b>Submitted!</b>\n\n<b>%s</b>\n\nYou'll be notified when approved.",
        "uz": "🎉 <b>Yuborildi!</b>\n\n<b>%s</b>\n\nTasdiqlanganda xabar beramiz.",
    },
    # ---------- COMPENSATION TYPES ----------
    "comp_equity": {"en": "📈 Equity", "uz": "📈 Ulush"},
    "comp_paid": {"en": "💵 Paid", "uz": "💵 Pullik"},
    "comp_negotiable": {"en": "🤝 Negotiable", "uz": "🤝 Kelishiladi"},
    "comp_volunteer": {"en": "🎁 Volunteer", "uz": "🎁 Ko'ngilli"},
    # ---------- LOCATION TYPES ----------
    "loc_remote": {"en": "🌍 Remote", "uz": "🌍 Masofaviy"},
    "loc_onsite": {"en": "🏢 On-site", "uz": "🏢 Ofisda"},
    "loc_hybrid": {"en": "🔄 Hybrid", "uz": "🔄 Aralash"},
    # ---------- MY REQUESTS ----------
    "my_requests_title": {"en": "📋 <b>My Requests</b>\n\n", "uz": "📋 <b>Mening e'lonlarim</b>\n\n"},
    "no_requests_yet": {
        "en": "📋 No requests yet.\n\nUse /post to create one!",
        "uz": "📋 Hali e'lon yo'q.\n\nYaratish: /post",
    },
    "status_pending": {"en": "🟡 Pending", "uz": "🟡 Kutilmoqda"},
    "status_approved": {"en": "🟢 Approved", "uz": "🟢 Tasdiqlangan"},
    "status_rejected": {"en": "🔴 Rejected", "uz": "🔴 Rad etilgan"},
    "status_closed": {"en": "⚫ Closed", "uz": "⚫ Yopilgan"},
    "status_label": {"en": "Status:", "uz": "Holat:"},
    "responses_label": {"en": "Responses:", "uz": "Javoblar:"},
    "views_label": {"en": "Views:", "uz": "Ko'rishlar:"},
    "rejection_reason": {"en": "❌ <b>Reason:</b>", "uz": "❌ <b>Sabab:</b>"},
    "btn_close_request": {"en": "🔒 Close", "uz": "🔒 Yopish"},
    "request_closed": {"en": "✅ Request closed.", "uz": "✅ E'lon yopildi."},
    "request_not_found": {"en": "Request not found.", "uz": "E'lon topilmadi."},
    # ---------- RESOURCES ----------
    "resources_title": {
        "en": "📚 <b>Resources</b>\n\nSelect a category:",
        "uz": "📚 <b>Resurslar</b>\n\nKategoriyani tanlang:",
    },
    "no_resources": {"en": "No resources in this category.", "uz": "Bu kategoriyada resurslar yo'q."},
    "no_resources_available": {
        "en": "📭 No resources available at the moment.",
        "uz": "📭 Hozircha resurslar yo'q.",
    },
    "btn_open_resource": {"en": "🔗 Open", "uz": "🔗 Ochish"},
    # ---------- PROFILE ----------
    "profile_title": {"en": "👤 <b>Your Profile</b>\n\n", "uz": "👤 <b>Sizning profilingiz</b>\n\n"},
    "profile_name": {"en": "📛 Name:", "uz": "📛 Ism:"},
    "profile_username": {"en": "👤 Username:", "uz": "👤 Username:"},
    "profile_age": {"en": "Age:", "uz": "Yosh:"},
    "profile_city": {"en": "City:", "uz": "Shahar:"},
    "profile_profession": {"en": "Profession:", "uz": "Kasb:"},
    "profile_company": {"en": "🏢 Company:", "uz": "🏢 Kompaniya:"},
    "profile_bio": {"en": "📝 Bio:", "uz": "📝 Bio:"},
    "not_set": {"en": "Not set", "uz": "Ko'rsatilmagan"},
    "btn_edit_profile": {"en": "✏️ Edit", "uz": "✏️ Tahrirlash"},
    "edit_what": {"en": "What to update?", "uz": "Nimani o'zgartirish?"},
    "btn_company_name": {"en": "🏢 Company", "uz": "🏢 Kompaniya"},
    "btn_bio": {"en": "📝 Bio", "uz": "📝 Bio"},
    "btn_linkedin": {"en": "🔗 LinkedIn", "uz": "🔗 LinkedIn"},
    "enter_company": {"en": "Enter company name:", "uz": "Kompaniya nomini kiriting:"},
    "enter_bio": {"en": "Enter your bio:", "uz": "O'zingiz haqingizda yozing:"},
    "enter_linkedin": {"en": "Enter LinkedIn URL:", "uz": "LinkedIn havolasini kiriting:"},
    "profile_updated": {"en": "✅ Updated!", "uz": "✅ Yangilandi!"},
    # ---------- RESPONSES ----------
    "already_responded": {"en": "You've already responded.", "uz": "Siz allaqachon javob bergansiz."},
    "request_unavailable": {"en": "This request is unavailable.", "uz": "Bu e'lon mavjud emas."},
    "interest_sent": {"en": "✅ Your interest sent to %s!", "uz": "✅ Qiziqishingiz %s ga yuborildi!"},
    "new_response_title": {"en": "🎉 <b>New Response!</b>\n\n", "uz": "🎉 <b>Yangi javob!</b>\n\n"},
    "someone_interested": {
        "en": "Someone is interested in:\n<b>%s</b>\n\n",
        "uz": "Kimdir sizning e'loningizga qiziqdi:\n<b>%s</b>\n\n",
    },
    "from_user": {"en": "👤 From:", "uz": "👤 Kimdan:"},
    "contact_hint": {"en": "💬 <i>Contact them directly!</i>", "uz": "💬 <i>To'g'ridan-to'g'ri bog'laning!</i>"},
    # ---------- EVENTS ----------
    "btn_events": {"en": "🎯 Events", "uz": "🎯 Tadbirlar"},
    "events_title": {
        "en": "🎯 <b>Upcoming Events</b>\n\nCompetitions, sessions, and meetups:",
        "uz": "🎯 <b>Tadbirlar</b>\n\nMusobaqalar, sessiyalar va uchrashuvlar:",
    },
    "no_events": {
        "en": "📭 No upcoming events at the moment.\n\nCheck back soon!",
        "uz": "📭 Hozircha rejalashtirilgan tadbirlar yo'q.\n\nTez orada yangilari qo'shiladi!",
    },
    "event_date": {"en": "📅 Date:", "uz": "📅 Sana:"},
    "event_location": {"en": "📍 Location:", "uz": "📍 Joylashuv:"},
    "btn_register_event": {"en": "📝 Register", "uz": "📝 Ro'yxatdan o'tish"},
    "admin_add_event": {"en": "➕ Add Event", "uz": "➕ Tadbir qo'shish"},
    "admin_event_title": {
        "en": "📌 <b>Step 1/6:</b> Event title:",
        "uz": "📌 <b>1/6-qadam:</b> Tadbir nomini kiriting:\n\n<i>Masalan: \"Startup Weekend Tashkent\" yoki \"Pitch Session #5\"</i>",
    },
    "admin_event_description": {
        "en": "📌 <b>Step 2/6:</b> Event description:",
        "uz": "📌 <b>2/6-qadam:</b> Tadbir haqida batafsil yozing:\n\n<i>Nima bo'ladi, kimlar uchun, nimalar o'rgatiladi...</i>",
    },
    "admin_event_image": {
        "en": "📌 <b>Step 3/6:</b> Send event image (poster):",
        "uz": "📌 <b>3/6-qadam:</b> Tadbir rasmini (poster) yuboring:",
    },
    "admin_event_date": {
        "en": "📌 <b>Step 4/6:</b> Event date and time:\n\n<i>Format: DD.MM.YYYY HH:MM</i>",
        "uz": "📌 <b>4/6-qadam:</b> Sana va vaqtni kiriting:\n\n<i>Format: KK.OO.YYYY SS:DD</i>\n<i>Masalan: 25.04.2025 18:00</i>",
    },
    "admin_event_location": {
        "en": "📌 <b>Step 5/6:</b> Event location:\n\n<i>Example: IT Park, Tashkent</i>",
        "uz": "📌 <b>5/6-qadam:</b> Joylashuvni kiriting:\n\n<i>Masalan: IT Park, Toshkent yoki Online (Zoom)</i>",
    },
    "admin_event_url": {
        "en": "📌 <b>Step 6/6:</b> Registration link:\n\n<i>Google Form, Telegram group, etc.</i>\n\nSend /skip to skip.",
        "uz": "📌 <b>6/6-qadam:</b> Ro'yxatdan o'tish havolasini kiriting:\n\n<i>Google Form, Telegram guruh va h.k.</i>\n\nO'tkazish: /skip",
    },
    "admin_event_created": {"en": "✅ <b>Event created!</b>\n\n%s", "uz": "✅ <b>Tadbir yaratildi!</b>\n\n%s"},
    "admin_event_date_error": {
        "en": "⚠️ Invalid date format. Use: DD.MM.YYYY HH:MM",
        "uz": "⚠️ Noto'g'ri format. Foydalaning: KK.OO.YYYY SS:DD",
    },
    "admin_events_list": {"en": "🎯 <b>Manage Events</b>", "uz": "🎯 <b>Tadbirlarni boshqarish</b>"},
    "admin_delete_event": {"en": "🗑 Delete", "uz": "🗑 O'chirish"},
    "admin_event_deleted": {"en": "✅ Event deleted.", "uz": "✅ Tadbir o'chirildi."},
    # ---------- ADMIN RESOURCES ----------
    "admin_resources_list": {"en": "📚 <b>Manage Resources</b>", "uz": "📚 <b>Resurslarni boshqarish</b>"},
    "admin_resource_category": {
        "en": "📁 Select category for the resource:",
        "uz": "📁 Resurs uchun kategoriyani tanlang:",
    },
    "admin_resource_title": {
        "en": "📌 <b>Step 1/3:</b> Resource title:\n\n<i>Example: \"Free Pitch Deck Template\"</i>",
        "uz": "📌 <b>1/3-qadam:</b> Resurs nomini kiriting:\n\n<i>Masalan: \"Bepul Pitch Deck shabloni\"</i>",
    },
    "admin_resource_description": {
        "en": "📌 <b>Step 2/3:</b> Resource description:\n\n<i>What is this resource about?</i>",
        "uz": "📌 <b>2/3-qadam:</b> Resurs haqida qisqacha yozing:\n\n<i>Bu resurs nima haqida?</i>",
    },
    "admin_resource_url": {
        "en": "📌 <b>Step 3/3:</b> Resource link:\n\n<i>URL to the resource</i>\n\nSend /skip to skip.",
        "uz": "📌 <b>3/3-qadam:</b> Resurs havolasini kiriting:\n\n<i>Resursga havola (URL)</i>\n\nO'tkazish: /skip",
    },
    "admin_resource_created": {"en": "✅ <b>Resource created!</b>\n\n%s", "uz": "✅ <b>Resurs yaratildi!</b>\n\n%s"},
    "admin_resource_deleted": {"en": "✅ Resource deleted.", "uz": "✅ Resurs o'chirildi."},
}


def set_lang(lang: str):
    _current["lang"] = lang if lang in ("en", "uz") else "uz"


def get_lang() -> str:
    return _current["lang"]


def get(key: str, *args) -> str:
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(_current["lang"]) or entry.get("uz") or key
    if args:
        try:
            return text % args
        except (TypeError, ValueError):
            return text
    return text


def get_compensation_type(type_: str) -> str:
    return {
        "equity": lambda: get("comp_equity"),
        "paid": lambda: get("comp_paid"),
        "negotiable": lambda: get("comp_negotiable"),
        "volunteer": lambda: get("comp_volunteer"),
    }.get(type_, lambda: type_.capitalize())()


def get_location_type(type_: str) -> str:
    return {
        "remote": lambda: get("loc_remote"),
        "onsite": lambda: get("loc_onsite"),
        "hybrid": lambda: get("loc_hybrid"),
    }.get(type_, lambda: type_.capitalize())()


def get_status(status: str) -> str:
    return {
        "pending": lambda: get("status_pending"),
        "approved": lambda: get("status_approved"),
        "rejected": lambda: get("status_rejected"),
        "closed": lambda: get("status_closed"),
    }.get(status, lambda: status)()

import json
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "8498800360:AAG4AgH2mtHsdjdQ-6hryXwFqYkjX9tS7r8"
ADMIN_ID = 7602621096
GROUPS_FILE = "groups.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_groups():
    try:
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_groups(groups: dict):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

joined_groups = load_groups()

pending_messages = {}
selected_groups = {}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Men xabar yuboruvchi botman.")


@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def catch_new_chat(message: types.Message):
    chat_id = str(message.chat.id)
    chat_title = message.chat.title or "NoName"

    if chat_id not in joined_groups:
        joined_groups[chat_id] = chat_title
        save_groups(joined_groups)
        print(f"✅ Yangi guruh qo‘shildi: {chat_title} ({chat_id})")


def make_group_keyboard(admin_id: int):
    keyboard = []
    selected = selected_groups.get(admin_id, [])
    for chat_id, title in joined_groups.items():
        # faqat -100 bilan boshlanadigan guruhlarni chiqaramiz
        if not chat_id.startswith("-100"):
            continue

        mark = "✅ " if chat_id in selected else ""
        keyboard.append([InlineKeyboardButton(
            text=f"{mark}{title}",
            callback_data=f"toggle:{chat_id}"
        )])
    keyboard.append([InlineKeyboardButton(text="📤 Yuborish", callback_data="send_all")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.message(F.chat.type == "private")
async def handle_admin_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return  # faqat admin ishlata oladi

    text = message.text
    if not text:
        return

    if not joined_groups:
        await message.answer("Bot hali hech qaysi guruhga qo‘shilmagan.")
        return

    pending_messages[message.from_user.id] = text
    selected_groups[message.from_user.id] = []

    reply_markup = make_group_keyboard(message.from_user.id)
    await message.answer("Qaysi guruhlarga yuborishni tanlang:", reply_markup=reply_markup)


# --- Tugmalarni bosganda guruhni tanlash ---
@dp.callback_query(F.data.startswith("toggle:"))
async def toggle_group(callback: types.CallbackQuery):
    admin_id = callback.from_user.id
    chat_id = callback.data.split(":")[1]

    if admin_id not in selected_groups:
        selected_groups[admin_id] = []

    if chat_id in selected_groups[admin_id]:
        selected_groups[admin_id].remove(chat_id)
    else:
        selected_groups[admin_id].append(chat_id)

    await callback.message.edit_reply_markup(reply_markup=make_group_keyboard(admin_id))
    await callback.answer()  # loadingni yopish uchun


# --- Yuborish tugmasi bosilganda ---
@dp.callback_query(F.data == "send_all")
async def send_all(callback: types.CallbackQuery):
    admin_id = callback.from_user.id

    if admin_id not in pending_messages:
        await callback.answer("❌ Xabar topilmadi.", show_alert=True)
        return

    msg = pending_messages[admin_id]
    groups = selected_groups.get(admin_id, [])

    if not groups:
        await callback.answer("❌ Guruh tanlanmagan.", show_alert=True)
        return

    count = 0
    for chat_id in groups:
        try:
            await bot.send_message(chat_id=int(chat_id), text=msg)
            count += 1
        except Exception as e:
            print(f"❌ Yuborilmadi {chat_id}: {e}")

    await callback.message.edit_text(f"✅ Xabar {count} ta guruhga yuborildi.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

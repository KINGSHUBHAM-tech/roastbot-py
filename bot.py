from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, os, random, re

API_ID = int(os.getenv("26891026"))
API_HASH = os.getenv("11aacc9305f8896ea752df2eadba2036")
BOT_TOKEN = os.getenv("7918688697:AAFyfB_0H5bm1Wq1hDOVR-rxeZpe28JO9VI")

app = Client("savage_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
DB_FILE = "modes.json"

def load_modes():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE) as f:
        return json.load(f)

def save_modes(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

modes = load_modes()
language_overrides = {}  # chat_id -> "eng" or None

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🔥 I’m your dark savage bot.\n"
        "🖤 Owned by @SUBHxCOSMO\n"
        "💬 Join support: @FALCONSUBHCHAT",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Join Support 🖤", url="https://t.me/FALCONSUBHCHAT")
        ]])
    )

@app.on_message(filters.command(["roaston", "complion", "rcon", "stop"], prefixes=".") & filters.me)
async def set_mode(client, message):
    chat_id = str(message.chat.id)
    cmd = message.command[0]
    if cmd == "roaston":
        modes[chat_id] = "roast"
        await message.reply("🔥 Roast mode activated.")
    elif cmd == "complion":
        modes[chat_id] = "compl"
        await message.reply("💀 Compliment mode activated.")
    elif cmd == "rcon":
        modes[chat_id] = "both"
        await message.reply("🎭 Random roast/compliment mode activated.")
    elif cmd == "stop":
        modes.pop(chat_id, None)
        language_overrides.pop(chat_id, None)
        await message.reply("🛑 Auto replies stopped.")
    save_modes(modes)

def generate_dynamic_text(mode, lang):
    if mode == "roast":
        if lang == "eng":
            return random.choice([
                "Your IQ needs a reboot.", 
                "You're proof that evolution can go backward.", 
                "You look like your personality was left in the sun too long."
            ])
        else:
            return random.choice([
                "Oye, teri soch 2 rupaye wali aur attitude 1000 ka 😂",
                "Tere jokes sunke WiFi bhi disconnect ho jaye.",
                "Bhai tu itna slow hai, snail bhi sharmaye."
            ])
    elif mode == "compl":
        if lang == "eng":
            return random.choice([
                "Your dark vibe is strangely attractive.",
                "You're beautifully twisted.",
                "Your smile could haunt dreams, in a good way."
            ])
        else:
            return random.choice([
                "Teri dark smile dil le gayi 💀",
                "Tu poison hai, par phir bhi chahiye.",
                "Itni dark vibe hai, bas bas pasand aa gayi."
            ])
    else:
        # rcon
        return generate_dynamic_text(random.choice(["roast", "compl"]), lang)

def is_english(text):
    letters = re.findall(r'[a-zA-Z]', text)
    return len(letters) > 0 and (len(letters) / max(len(text),1)) > 0.6

@app.on_message(filters.text & ~filters.command(["start"]))
async def auto_reply(client, message):
    chat_id = str(message.chat.id)
    if chat_id not in modes:
        return
    
    # Language override if replying to bot
    lang = "eng" if language_overrides.get(chat_id) == "eng" else None
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
        if is_english(message.text):
            language_overrides[chat_id] = "eng"
            lang = "eng"
    elif chat_id in language_overrides:
        language_overrides.pop(chat_id)

    mode = modes[chat_id]
    text = generate_dynamic_text(mode, lang or "hin")
    await message.reply_text(f"{text}\n\n— 🤖 Powered by @{(await app.get_me()).username}")

app.run()

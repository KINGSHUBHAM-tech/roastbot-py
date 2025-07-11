import logging
import requests
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Config
NUMLOOK_API_KEY = "num_live_nr9kxefWP1xBNk64EoNjysZcHKxHxE9ktF3e5WDp"
APILAYER_API_KEY = "uDSQF5qdEH1ig8OHgKwMVFOlHdySGYN6"
BOT_TOKEN = "7532994082:AAHVLyzK9coVgvCp-nwXL1MfPS0X57yZAmk"
REQUIRED_CHANNELS = ["@FALCONSUBH", "@FALCONSUBHCHAT"]
LOG_GROUP = "@FALCONSUBHCHAT"

# Setup
logging.basicConfig(level=logging.INFO)
banned_users = set()
user_limits = {}

# Force join checker
async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Force join check
    if not await is_user_joined(user_id, context):
        keyboard = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚫 You must join both channels to use this bot.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Send log to group
    text_log = (
        f"📥 New user started bot\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📛 Username: @{user.username or 'N/A'}\n"
        f"🌍 Language: {user.language_code or 'N/A'}"
    )
    try:
        await context.bot.send_message(LOG_GROUP, text_log)
    except Exception as e:
        logging.error(f"Failed to send log: {e}")

    # Main menu
    text = (
        "👋 Welcome to the Phone Number Info Bot!\n\n"
        "You can check details of any phone number via two servers:\n"
        "📡 SERVER1 (NumLook API)\n"
        "📡 SERVER2 (APIlayer API)\n"
        "😉 IF ANY SERVER DOESN'T REPLY OR RESPONSE\n THEN TRY CHANGING TO ANOTHER\n\n"
        "👤 Created by @FALCONSUBH\n"
    )
    keyboard = [
        [
            InlineKeyboardButton("SERVER1", callback_data="server1"),
            InlineKeyboardButton("SERVER2", callback_data="server2"),
        ],
        [InlineKeyboardButton("SUPPORT", url="https://t.me/FALCONSUBHCHAT")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Callback: check_join
async def handle_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_joined(user_id, context):
        await query.message.delete()
        await start(update, context)
    else:
        await query.message.reply_text("❗ You still haven't joined all required channels.")

# Callback: server buttons
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_user_joined(user_id, context):
        keyboard = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await query.message.reply_text("🚫 Join all channels to use the bot.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "server1":
        context.user_data["server"] = "server1"
        await query.message.reply_text("🟢 SERVER1 selected. Send a phone number (e.g., +12069220880)")
    elif query.data == "server2":
        context.user_data["server"] = "server2"
        await query.message.reply_text("🟢 SERVER2 selected. Send a phone number (e.g., +12069220880)")

# Number fetch handler
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Check banned
    if user_id in banned_users:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    # Force join
    if not await is_user_joined(user_id, context):
        keyboard = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚫 Join all channels to use the bot.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Check limit
    today = datetime.date.today()
    if user_id not in user_limits:
        user_limits[user_id] = {"date": today, "count": 0}
    elif user_limits[user_id]["date"] != today:
        user_limits[user_id] = {"date": today, "count": 0}

    if user_limits[user_id]["count"] >= 3:
        await update.message.reply_text("⚠️ Daily limit reached. You can fetch only 3 numbers per day.")
        return

    server = context.user_data.get("server")
    if not server:
        await update.message.reply_text("⚠️ Please choose a server first using /start.")
        return

    number = update.message.text.strip()
    if not number.startswith("+"):
        await update.message.reply_text("❗ Use valid number format with + (e.g., +12069220880)")
        return

    if server == "server1":
        url = f"https://api.numlookupapi.com/v1/validate/{number}?apikey={NUMLOOK_API_KEY}"
    else:
        url = f"http://apilayer.net/api/validate?access_key={APILAYER_API_KEY}&number={number}"

    try:
        res = requests.get(url)
        data = res.json()

        if "error" in data:
            await update.message.reply_text(f"❌ Error: {data['error']['info']}")
            return

        # Count usage
        user_limits[user_id]["count"] += 1

        msg = (
            f"🔍 **{'NumLook' if server == 'server1' else 'APIlayer'} Result**\n"
            f"📞 Number: {data.get('international_format')}\n"
            f"🌐 Country: {data.get('country_name')} ({data.get('country_code')})\n"
            f"🏙️ Location: {data.get('location') or 'N/A'}\n"
            f"📱 Carrier: {data.get('carrier')}\n"
            f"📲 Line Type: {data.get('line_type') or 'N/A'}"
        )

        await update.message.reply_text(msg)
    except Exception as e:
        logging.error(f"Error fetching number: {e}")
        await update.message.reply_text("❌ Failed to fetch number info.")

# Admin: !ban and !unban
async def ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()
    is_ban = text.startswith("!ban")
    is_unban = text.startswith("!unban")

    if not is_ban and not is_unban:
        return

    try:
        parts = text.split(" ", 1)
        target = int(parts[1].strip().lstrip("@"))
    except:
        await update.message.reply_text("❗ Usage: !ban <user_id> or !unban <user_id>")
        return

    if is_ban:
        banned_users.add(target)
        await update.message.reply_text(f"✅ User `{target}` has been banned.")
    else:
        banned_users.discard(target)
        await update.message.reply_text(f"✅ User `{target}` has been unbanned.")

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^(server1|server2)$"))
    app.add_handler(CallbackQueryHandler(handle_check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^!(ban|unban) "), ban_unban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_polling()

if __name__ == "__main__":
    main()
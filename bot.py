import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging
logging.basicConfig(level=logging.INFO)

# API KEYS
NUMLOOK_API_KEY = "num_live_nr9kxefWP1xBNk64EoNjysZcHKxHxE9ktF3e5WDp"
APILAYER_API_KEY = "uDSQF5qdEH1ig8OHgKwMVFOlHdySGYN6"
BOT_TOKEN = "7532994082:AAHVLyzK9coVgvCp-nwXL1MfPS0X57yZAmk"

REQUIRED_CHANNELS = ["@FALCONSUBH", "@FALCONSUBHCHAT"]

# Force join check
async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logging.error(f"Error checking membership in {channel}: {e}")
            return False
    return True

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_user_joined(user_id, context):
        buttons = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "🚫 You must join both channels to use this bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

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

# Handle join check button
async def handle_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await is_user_joined(user_id, context):
        await query.message.delete()
        await start(update, context)  # Send the /start content
    else:
        await query.message.reply_text("❗ You still haven't joined all required channels.")

# Handle server button
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not await is_user_joined(user_id, context):
        buttons = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await query.message.reply_text("🚫 Please join both channels to use the bot.", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if query.data == "server1":
        context.user_data["server"] = "server1"
        await query.message.reply_text("🟢 SERVER1 selected. Send a phone number (e.g., +12069220880)")
    elif query.data == "server2":
        context.user_data["server"] = "server2"
        await query.message.reply_text("🟢 SERVER2 selected. Send a phone number (e.g., +12069220880)")

# Handle number
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_joined(user_id, context):
        buttons = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚫 You must join both channels first.", reply_markup=InlineKeyboardMarkup(buttons))
        return

    server = context.user_data.get("server")
    if not server:
        await update.message.reply_text("⚠️ Please choose a server first using /start.")
        return

    number = update.message.text.strip()

    if not number.startswith("+"):
        await update.message.reply_text("❗ Please provide a valid number with country code (e.g., +12069220880)")
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

        if server == "server1":
            msg = (
                f"🔍 **NumLook Result**\n"
                f"📞 Number: {data.get('international_format')}\n"
                f"🌐 Country: {data.get('country_name')} ({data.get('country_code')})\n"
                f"🏙️ Location: {data.get('location')}\n"
                f"📱 Carrier: {data.get('carrier')}\n"
                f"📲 Line Type: {data.get('line_type')}"
            )
        else:
            msg = (
                f"🔍 **APIlayer Result**\n"
                f"📞 Number: {data.get('international_format')}\n"
                f"🌐 Country: {data.get('country_name')} ({data.get('country_code')})\n"
                f"🏙️ Location: {data.get('location') or 'N/A'}\n"
                f"📱 Carrier: {data.get('carrier')}\n"
                f"📲 Line Type: {data.get('line_type') or 'N/A'}"
            )

        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch number info. Please try again later.")

# MAIN FUNCTION
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^(server1|server2)$"))
    app.add_handler(CallbackQueryHandler(handle_check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_polling()

if __name__ == "__main__":
    main()
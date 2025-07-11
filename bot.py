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

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Welcome to the Phone Number Info Bot!\n\n"
        "You can check details of any phone number via two servers:\n"
        "📡 SERVER1 (NumLook API)\n"
        "📡 SERVER2 (APIlayer API)\n\n"
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

# STORE ACTIVE SERVER IN CONTEXT
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "server1":
        context.user_data["server"] = "server1"
        await query.message.reply_text("🟢 SERVER1 selected. Send a phone number (e.g., +12069220880)")
    elif query.data == "server2":
        context.user_data["server"] = "server2"
        await query.message.reply_text("🟢 SERVER2 selected. Send a phone number (e.g., +12069220880)")

# HANDLE NUMBER MESSAGE
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = context.user_data.get("server")
    if not server:
        await update.message.reply_text("⚠️ Please choose a server first using /start.")
        return

    number = update.message.text.strip()

    if not number.startswith("+"):
        await update.message.reply_text("❗ Please provide a valid number with country code (e.g., +12069220880)")
        return

    if server == "server1":
        # NumLook API
        url = f"https://api.numlookupapi.com/v1/validate/{number}?apikey={NUMLOOK_API_KEY}"
    else:
        # APIlayer API
        url = f"http://apilayer.net/api/validate?access_key={APILAYER_API_KEY}&number={number}"

    try:
        res = requests.get(url)
        data = res.json()

        if "error" in data:
            await update.message.reply_text(f"❌ Error: {data['error']['info']}")
            return

        # Build response text
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
    import os

    TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Render.com
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_polling()

if __name__ == "__main__":
    main() 
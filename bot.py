import logging, requests, datetime, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("7532994082:AAHVLyzK9coVgvCp-nwXL1MfPS0X57yZAmk", "")
NUMLOOK_API_KEY = os.getenv("num_live_nr9kxefWP1xBNk64EoNjysZcHKxHxE9ktF3e5WDp", "")
APILAYER_API_KEY = os.getenv("uDSQF5qdEH1ig8OHgKwMVFOlHdySGYN6 ", "")
ABSTRACT_API_KEY = os.getenv("ad2328956d0a4caf818fdb4c042a1bfd", "")

REQUIRED_CHANNELS = ["@FALCONSUBH", "@FALCONSUBHCHAT"]
LOG_GROUP = "@OGPAYOSINT"
ADMIN_IDS = {5848851070, 1350027752}
PASSWORD = "@SUBHxCOSMO"

banned_users = set()
user_limits = {}
users_started = set()

logging.basicConfig(level=logging.INFO)

# -------------- FUNCTIONS ----------------
async def is_user_joined(uid, ctx):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(chat_id=ch, user_id=uid)
            if m.status in ("left", "kicked"):
                return False
        except:
            return False
    return True

async def private_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return update.effective_chat.type == "private"

# -------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    user = update.effective_user
    is_new = user.id not in users_started
    users_started.add(user.id)

    if not await is_user_joined(user.id, context):
        kb = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚫 *You must join both channels first.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    if is_new:
        await context.bot.send_message(LOG_GROUP,
            f"📥 *New User Started Bot!*\n"
            f"👤 [{user.full_name}](tg://user?id={user.id})\n"
            f"🆔 `{user.id}`\n"
            f"🌐 Username: @{user.username or 'N/A'}",
            parse_mode="Markdown")

    kb = [
        [
            InlineKeyboardButton("🔹 SERVER1", callback_data="server1"),
            InlineKeyboardButton("🔸 SERVER2", callback_data="server2"),
            InlineKeyboardButton("🔺 SERVER3", callback_data="server3")
        ],
        [InlineKeyboardButton("💬 SUPPORT", url="https://t.me/FALCONSUBHCHAT")]
    ]
    await update.message.reply_text("👋 *Welcome to the Phone Number Info Bot!*\n\nPlease select a server to proceed.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def handle_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    query = update.callback_query
    await query.answer()
    if await is_user_joined(query.from_user.id, context):
        await query.message.delete()
        await start(update, context)
    else:
        await query.message.reply_text("❗ *You still haven't joined required channels.*", parse_mode="Markdown")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    query = update.callback_query
    await query.answer()
    if not await is_user_joined(query.from_user.id, context):
        kb = [[InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]]
        await query.message.reply_text("🚫 *Please join required channels.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return
    context.user_data["server"] = query.data
    await query.message.reply_text(f"✅ *{query.data.upper()} selected.*\n\nSend a phone number (e.g., +1234567890)", parse_mode="Markdown")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    user = update.effective_user
    uid = user.id
    users_started.add(uid)

    if uid in banned_users:
        await update.message.reply_text("🚫 *You are banned from using this bot.*", parse_mode="Markdown")
        return

    if not await is_user_joined(uid, context):
        await update.message.reply_text("🚫 *Please join required channels first.*", parse_mode="Markdown")
        return

    today = datetime.date.today()
    ul = user_limits.get(uid)
    if not ul or ul['date'] != today:
        user_limits[uid] = {'date': today, 'count': 0}
    if user_limits[uid]['count'] >= 3:
        await update.message.reply_text("⚠️ *Daily limit reached (3 lookups).*", parse_mode="Markdown")
        return

    server = context.user_data.get("server")
    if not server:
        await update.message.reply_text("⚠️ *Use /start to select a server first.*", parse_mode="Markdown")
        return

    number = update.message.text.strip()
    if not number.startswith("+"):
        await update.message.reply_text("❗ *Use format: +1234567890*", parse_mode="Markdown")
        return

    if server == "server1":
        url = f"https://api.numlookupapi.com/v1/validate/{number}?apikey={NUMLOOK_API_KEY}"
    elif server == "server2":
        url = f"http://apilayer.net/api/validate?access_key={APILAYER_API_KEY}&number={number}"
    else:
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&phone={number}"

    try:
        res = requests.get(url)
        data = res.json()
        user_limits[uid]['count'] += 1

        if server == "server3":
            fmt = (
                f"🔍 *Abstract API Result*\n"
                f"📞 *Number:* `{data.get('international') or number}`\n"
                f"🌍 *Country:* {data.get('country', {}).get('name', 'N/A')} ({data.get('country', {}).get('code', 'N/A')})\n"
                f"🏙️ *Location:* {data.get('location') or 'N/A'}\n"
                f"📱 *Carrier:* {data.get('carrier') or 'N/A'}\n"
                f"📲 *Line Type:* {data.get('type') or 'N/A'}"
            )
        else:
            prov = "NumLook" if server == "server1" else "APIlayer"
            fmt = (
                f"🔍 *{prov} Result*\n"
                f"📞 *Number:* `{data.get('international_format') or number}`\n"
                f"🌍 *Country:* {data.get('country_name', 'N/A')} ({data.get('country_code', 'N/A')})\n"
                f"🏙️ *Location:* {data.get('location') or 'N/A'}\n"
                f"📱 *Carrier:* {data.get('carrier') or 'N/A'}\n"
                f"📲 *Line Type:* {data.get('line_type') or 'N/A'}"
            )

        await update.message.reply_text(fmt, parse_mode="Markdown")

        log_msg = (
            f"📡 *New Lookup Request!*\n\n"
            f"👤 *User:* [{user.full_name}](tg://user?id={uid})\n"
            f"🆔 *User ID:* `{uid}`\n"
            f"🌐 *Username:* @{user.username or 'N/A'}\n"
            f"📞 *Queried Number:* `{number}`\n"
            f"🛠 *Server:* `{server.upper()}`\n"
            f"🗓 *Time:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 *Lookup Count Today:* {user_limits[uid]['count']}/3"
        )
        await context.bot.send_message(LOG_GROUP, log_msg, parse_mode="Markdown")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ *Failed to fetch number info.*", parse_mode="Markdown")

# ---------------- RUN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^server"))
    app.add_handler(CallbackQueryHandler(handle_check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_polling()

if __name__ == "__main__":
    main()

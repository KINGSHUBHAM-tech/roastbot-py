import logging, requests, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# 🔐 Configuration
NUMLOOK_API_KEY = "num_live_nr9kxefWP1xBNk64EoNjysZcHKxHxE9ktF3e5WDp"
APILAYER_API_KEY = "uDSQF5qdEH1ig8OHgKwMVFOlHdySGYN6"
ABSTRACT_API_KEY = "ad2328956d0a4caf818fdb4c042a1bfd"
BOT_TOKEN = "7532994082:AAHVLyzK9coVgvCp-nwXL1MfPS0X57yZAmk"

REQUIRED_CHANNELS = ["@FALCONSUBH", "@FALCONSUBHCHAT"]
LOG_GROUP = "@OGPAYOSINT"
ADMIN_IDS = {5848851070, 1350027752}
PASSWORD = "@SUBHxCOSMO"

# ⚙️ Runtime storage
banned_users = set()
user_limits = {}
users_started = set()

# 🔐 Join check
async def is_user_joined(uid, ctx):
    for ch in REQUIRED_CHANNELS:
        try:
            st = await ctx.bot.get_chat_member(chat_id=ch, user_id=uid)
            if st.status in ("left", "kicked"):
                return False
        except:
            return False
    return True

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_started.add(user.id)

    if not await is_user_joined(user.id, context):
        kb = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        return await update.message.reply_text("🚫 Join both channels first.", reply_markup=InlineKeyboardMarkup(kb))

    await context.bot.send_message(LOG_GROUP, f"📥 New User: {user.full_name} | ID: `{user.id}` | @{user.username or 'N/A'}", parse_mode="Markdown")

    kb = [
        [
            InlineKeyboardButton("SERVER1", callback_data="server1"),
            InlineKeyboardButton("SERVER2", callback_data="server2"),
            InlineKeyboardButton("SERVER3", callback_data="server3")
        ],
        [InlineKeyboardButton("SUPPORT", url="https://t.me/FALCONSUBHCHAT")]
    ]
    await update.message.reply_text("👋 Welcome to Phone Info Bot!", reply_markup=InlineKeyboardMarkup(kb))

# ✅ Channel join verify
async def handle_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_user_joined(query.from_user.id, context):
        await query.message.delete()
        await start(update, context)
    else:
        await query.message.reply_text("❗ Still not joined both channels.")

# 📡 Server selection
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await is_user_joined(query.from_user.id, context):
        kb = [[InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]]
        return await query.message.reply_text("🚫 Please join required channels.", reply_markup=InlineKeyboardMarkup(kb))

    context.user_data["server"] = query.data
    await query.message.reply_text(f"✅ {query.data.upper()} selected. Send phone number.")

# 🔍 Number lookup
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    users_started.add(uid)

    if uid in banned_users:
        return await update.message.reply_text("🚫 You are banned.")
    if not await is_user_joined(uid, context):
        return await update.message.reply_text("🚫 Join channels to continue.")

    today = datetime.date.today()
    if uid not in user_limits or user_limits[uid]['date'] != today:
        user_limits[uid] = {'date': today, 'count': 0}
    if user_limits[uid]['count'] >= 3:
        return await update.message.reply_text("⚠️ Daily limit reached (3 lookups).")

    server = context.user_data.get("server")
    if not server:
        return await update.message.reply_text("⚠️ Use /start to pick a server.")

    number = update.message.text.strip()
    if not number.startswith("+"):
        return await update.message.reply_text("❗ Format: +1234567890")

    # API URLs
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
            msg = (
                f"*Abstract Result*\n"
                f"📞 {data.get('international')}\n"
                f"🌐 {data.get('country', {}).get('name')}\n"
                f"📍 {data.get('location')}\n"
                f"📱 {data.get('carrier')}\n"
                f"📶 {data.get('type')}"
            )
        else:
            msg = (
                f"*{server.upper()} Result*\n"
                f"📞 {data.get('international_format')}\n"
                f"🌐 {data.get('country_name')} ({data.get('country_code')})\n"
                f"📍 {data.get('location')}\n"
                f"📱 {data.get('carrier')}\n"
                f"📶 {data.get('line_type')}"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
        await context.bot.send_message(LOG_GROUP, f"📊 Lookup by {uid} | Number: `{number}` | Server: `{server.upper()}`", parse_mode="Markdown")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Fetch failed.")

# 🧑‍⚖️ Ban/Unban
async def ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return await update.message.reply_text("❌ Not authorized.")
    try:
        parts = update.message.text.split()
        cmd, target = parts[0], int(parts[1].lstrip("@"))
        if cmd == "!ban":
            banned_users.add(target)
            await update.message.reply_text(f"✅ Banned user `{target}`", parse_mode="Markdown")
        elif cmd == "!unban":
            banned_users.discard(target)
            await update.message.reply_text(f"✅ Unbanned user `{target}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❗ Usage: !ban <user_id> or !unban <user_id>")

# 📢 /broadcast
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")
    await update.message.reply_text("Send the broadcast message:")
    context.user_data["awaiting_broadcast"] = True

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.pop("awaiting_broadcast", False):
        return await handle_number(update, context)
    msg = update.message.text
    count = 0
    for uid in users_started:
        try:
            await context.bot.send_message(uid, msg)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
    await context.bot.send_message(LOG_GROUP, f"📢 Broadcast:\n{msg}")

# 🛡️ /apanel
async def apanel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 Enter admin panel password:")
    context.user_data["awaiting_apanel"] = True

async def apanel_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.pop("awaiting_apanel", False):
        return await handle_number(update, context)
    if update.message.text.strip() != PASSWORD:
        return await update.message.reply_text("❌ Incorrect password.")
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]
    ]
    for aid in ADMIN_IDS:
        await context.bot.send_message(aid, f"👤 Admin Request from `{user.full_name}` | ID: `{user.id}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    await update.message.reply_text("⏳ Sent for approval...")

async def apanel_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    if "approve" in data or "reject" in data:
        target = int(data.split("_")[1])
        if "approve" in data:
            ADMIN_IDS.add(target)
            await context.bot.send_message(target, "✅ You are now an admin.")
            await context.bot.send_message(LOG_GROUP, f"🟢 Approved admin `{target}`")
        else:
            await context.bot.send_message(target, "❌ Your request was rejected.")
            await context.bot.send_message(LOG_GROUP, f"🔴 Rejected admin `{target}`")

# 📚 /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    help_text = (
        "📖 *Help Menu*\n\n"
        "👥 *User Commands:*\n"
        "• /start – Start and select server\n"
        "• /help – View this help menu\n"
        "• Send number (e.g., +1234567890)\n"
    )
    if uid in ADMIN_IDS:
        help_text += (
            "\n🛡️ *Admin Commands:*\n"
            "• /broadcast – Send message to all users\n"
            "• /apanel – Request admin panel access\n"
            "• !ban <user_id> – Ban user\n"
            "• !unban <user_id> – Unban user\n"
        )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# 🔁 main()
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("broadcast", broadcast_start))
    app.add_handler(CommandHandler("apanel", apanel_start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^server"))
    app.add_handler(CallbackQueryHandler(handle_check_join, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(apanel_response, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^!(ban|unban) "), ban_unban))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r".+"), broadcast_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.add_handler(MessageHandler(filters.TEXT, apanel_password))
    app.run_polling()

if __name__ == "__main__":
    main()
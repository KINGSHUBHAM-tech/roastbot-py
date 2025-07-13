import logging, requests, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# Configuration
NUMLOOK_API_KEY = "num_live_nr9kxefWP1xBNk64EoNjysZcHKxHxE9ktF3e5WDp"
APILAYER_API_KEY = "uDSQF5qdEH1ig8OHgKwMVFOlHdySGYN6"
ABSTRACT_API_KEY = "ad2328956d0a4caf818fdb4c042a1bfd"
BOT_TOKEN = "7532994082:AAHVLyzK9coVgvCp-nwXL1MfPS0X57yZAmk"

REQUIRED_CHANNELS = ["@FALCONSUBH", "@FALCONSUBHCHAT"]
LOG_GROUP = "@OGPAYOSINT"
ADMIN_IDS = {5848851070, 1350027752}
PASSWORD = "@SUBHxCOSMO"

banned_users = set()
user_limits = {}
users_started = set()

logging.basicConfig(level=logging.INFO)

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
    if update.effective_chat.type != "private":
        return False
    return True

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context):
        return
    user = update.effective_user
    users_started.add(user.id)

    if not await is_user_joined(user.id, context):
        kb = [
            [InlineKeyboardButton("Join @FALCONSUBH", url="https://t.me/FALCONSUBH")],
            [InlineKeyboardButton("Join @FALCONSUBHCHAT", url="https://t.me/FALCONSUBHCHAT")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚫 You must join both channels first.", reply_markup=InlineKeyboardMarkup(kb))
        return

    await context.bot.send_message(LOG_GROUP,
        f"📥 New User Started Bot\n👤 {user.full_name}\n🆔 `{user.id}`\nUsername: @{user.username or 'N/A'}",
        parse_mode="Markdown")

    kb = [
        [
            InlineKeyboardButton("SERVER1", callback_data="server1"),
            InlineKeyboardButton("SERVER2", callback_data="server2"),
            InlineKeyboardButton("SERVER3", callback_data="server3")
        ],
        [InlineKeyboardButton("SUPPORT", url="https://t.me/FALCONSUBHCHAT")]
    ]
    await update.message.reply_text("👋 Welcome to the Phone Number Info Bot!", reply_markup=InlineKeyboardMarkup(kb))

# Check join
async def handle_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    query = update.callback_query
    await query.answer()
    if await is_user_joined(query.from_user.id, context):
        await query.message.delete()
        await start(update, context)
    else:
        await query.message.reply_text("❗ You still haven't joined required channels.")

# Server selection
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    query = update.callback_query
    await query.answer()
    if not await is_user_joined(query.from_user.id, context):
        kb = [[InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]]
        await query.message.reply_text("🚫 Please join channels.", reply_markup=InlineKeyboardMarkup(kb))
        return
    context.user_data["server"] = query.data
    await query.message.reply_text(f"✅ {query.data.upper()} selected. Now send a phone number (e.g., +1234567890)")

# Lookup logic
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    user = update.effective_user
    uid = user.id
    users_started.add(uid)

    if uid in banned_users:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    if not await is_user_joined(uid, context):
        await update.message.reply_text("🚫 Please join required channels first.")
        return

    today = datetime.date.today()
    ul = user_limits.get(uid)
    if not ul or ul['date'] != today:
        user_limits[uid] = {'date': today, 'count': 0}
    if user_limits[uid]['count'] >= 3:
        await update.message.reply_text("⚠️ Daily limit reached (3 lookups).")
        return

    server = context.user_data.get("server")
    if not server:
        await update.message.reply_text("⚠️ Use /start to select a server first.")
        return

    number = update.message.text.strip()
    if not number.startswith("+"):
        await update.message.reply_text("❗ Use format: +1234567890")
        return

    # Build API URL
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

        # Format response
        if server == "server3":
            fmt = (
                f"🔍 **Abstract API Result**\n"
                f"📞 *Number:* {data.get('international') or number}\n"
                f"🌐 *Country:* {data.get('country',{}).get('name','N/A')} ({data.get('country',{}).get('code','N/A')})\n"
                f"🏙️ *Location:* {data.get('location') or 'N/A'}\n"
                f"📱 *Carrier:* {data.get('carrier') or 'N/A'}\n"
                f"📲 *Line Type:* {data.get('type') or 'N/A'}"
            )
        else:
            prov = "NumLook" if server == "server1" else "APIlayer"
            fmt = (
                f"🔍 **{prov} Result**\n"
                f"📞 *Number:* {data.get('international_format') or number}\n"
                f"🌐 *Country:* {data.get('country_name','N/A')} ({data.get('country_code','N/A')})\n"
                f"🏙️ *Location:* {data.get('location') or 'N/A'}\n"
                f"📱 *Carrier:* {data.get('carrier') or 'N/A'}\n"
                f"📲 *Line Type:* {data.get('line_type') or 'N/A'}"
            )
        await update.message.reply_text(fmt, parse_mode="Markdown")

        # Log lookup
        await context.bot.send_message(LOG_GROUP,
            f"📊 *Number Lookup*\n👤 `{user.full_name}` | ID: `{uid}`\n📞 `{number}` | Server: `{server.upper()}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Failed to fetch number info.")

# Admin ban/unban
async def ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized.")
        return
    parts = update.message.text.split()
    if len(parts) != 2 or not parts[1].lstrip("@").isdigit():
        return await update.message.reply_text("❗ Usage: !ban <user_id> or !unban <user_id>")
    tgt = int(parts[1].lstrip("@"))
    if parts[0] == "!ban":
        banned_users.add(tgt)
        await update.message.reply_text(f"✅ Banned `{tgt}`", parse_mode="Markdown")
    else:
        banned_users.discard(tgt)
        await update.message.reply_text(f"✅ Unbanned `{tgt}`", parse_mode="Markdown")

# Broadcast
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only.")
        return
    await update.message.reply_text("📢 Enter broadcast message:")
    context.user_data["awaiting_broadcast"] = True

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    if not context.user_data.pop("awaiting_broadcast", None):
        return await handle_number(update, context)
    msg = update.message.text
    count = 0
    for uid in users_started:
        try:
            await context.bot.send_message(uid, msg)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast to {count} users.")
    await context.bot.send_message(LOG_GROUP, f"📢 Broadcast:\n{msg}")

# Admin panel
async def apanel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    await update.message.reply_text("🔑 Enter admin password:")
    context.user_data["awaiting_apanel"] = True

async def apanel_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    if not context.user_data.pop("awaiting_apanel", None):
        return await handle_number(update, context)
    if update.message.text.strip() != PASSWORD:
        return await update.message.reply_text("❌ Incorrect password.")
    requester = update.effective_user
    kb = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{requester.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{requester.id}")]
    ]
    for aid in ADMIN_IDS:
        await context.bot.send_message(aid,
            f"🔐 Admin request from `{requester.full_name}` (ID: `{requester.id}`)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb))
    await update.message.reply_text("⏳ Request sent for approval…")

async def apanel_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    query = update.callback_query
    await query.answer()
    data = query.data
    if not (data.startswith("approve_") or data.startswith("reject_")):
        return
    target = int(data.split("_")[1])
    approver = query.from_user.id
    if approver not in ADMIN_IDS:
        return
    if data.startswith("approve_"):
        ADMIN_IDS.add(target)
        await context.bot.send_message(target, "✅ Your admin request was approved.")
        await context.bot.send_message(LOG_GROUP, f"🟢 Admin approved `{target}` by `{approver}`")
    else:
        await context.bot.send_message(target, "❌ Your admin request was rejected.")
        await context.bot.send_message(LOG_GROUP, f"🔴 Admin rejected `{target}` by `{approver}`")

# /help dynamic
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await private_only(update, context): return
    uid = update.effective_user.id
    txt = (
        "📖 *Help Menu*\n\n"
        "👤 *User Commands:*\n"
        "• /start — Start bot & pick server\n"
        "• /help — Show this menu\n"
        "• Send phone number after selecting a server\n"
    )
    if uid in ADMIN_IDS:
        txt += (
            "\n🛡️ *Admin Commands:*\n"
            "• /broadcast — Send message to all users\n"
            "• /apanel — Request admin access\n"
            "• !ban <user_id> — Ban a user\n"
            "• !unban <user_id> — Unban a user\n"
        )
    await update.message.reply_text(txt, parse_mode="Markdown")

# Run
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("broadcast", broadcast_start))
    app.add_handler(CommandHandler("apanel", apanel_start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^server"))
    app.add_handler(CallbackQueryHandler(handle_check_join, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(apanel_response, pattern="^(approve_|reject_)"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^!(ban|unban) "), ban_unban))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r".+"), broadcast_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.add_handler(MessageHandler(filters.TEXT, apanel_password))

    app.run_polling()

if __name__ == "__main__":
    main()
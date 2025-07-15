import os
import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CAPITAL, ENTRY, SL, ASSET = range(4)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Welcome to Risk Manager Bot!\n\nLet's calculate your trade.\nEnter your capital in USD:"
    )
    return CAPITAL

async def capital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id] = {"capital": float(update.message.text)}
    await update.message.reply_text("Enter entry price:")
    return ENTRY

async def entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id]["entry"] = float(update.message.text)
    await update.message.reply_text("Enter stop loss price:")
    return SL

async def sl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id]["sl"] = float(update.message.text)
    await update.message.reply_text("Enter instrument (XAUUSD or BTC):")
    return ASSET

async def asset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = user_data_store[update.effective_user.id]
    asset = update.message.text.upper()
    data["asset"] = asset

    capital = data["capital"]
    entry = data["entry"]
    sl = data["sl"]
    risk = round(capital * 0.05, 2)
    risk_per_unit = abs(entry - sl)

    if risk_per_unit == 0:
        await update.message.reply_text("Stop loss can't be equal to entry. Try again.")
        return ConversationHandler.END

    position_size = round(risk / risk_per_unit, 4)
    target_price = entry + 2 * (entry - sl) if entry > sl else entry - 2 * (sl - entry)
    reward = round(risk * 2, 2)

    msg = f"\n✅ Trade Summary ({asset})\n" \
          f"Capital: ${capital}\n" \
          f"Risk (5%): ${risk}\n" \
          f"Entry: {entry}\n" \
          f"Stop Loss: {sl}\n" \
          f"Position Size: {position_size} units\n" \
          f"Target Price (1:2): {round(target_price, 2)}\n" \
          f"Expected Reward: ${reward}"

    await update.message.reply_text(msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Trade setup cancelled.")
    return ConversationHandler.END

def main() -> None:
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capital)],
            ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, entry)],
            SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sl)],
            ASSET: [MessageHandler(filters.TEXT & ~filters.COMMAND, asset)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()

import asyncio
import requests
import threading
import re
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# === Налаштування ===
TELEGRAM_TOKEN = '7032915019:AAEZ7AteszlwPdCEsNiMGGN5ndKciMcO9XY'
CHAT_ID = 444448229
START_PRICE = 4000
STEP = 20

last_notified_price = START_PRICE

# === Flask для UptimeRobot ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот працює 24/7"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# === Отримання ціни ETH ===
def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return float(data['ethereum']['usd'])

# === Обробка команди /status або !status ===
async def send_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_eth_price()
    await update.message.reply_text(f"🔹 Поточна ціна ETH: ${price:.2f}")

# === Монітор ціни ETH ===
async def monitor_price(application):
    global last_notified_price
    while True:
        try:
            price = get_eth_price()
            print(f"[INFO] Поточна ціна ETH: ${price:.2f}")

            # Якщо ціна піднялася на STEP або більше
            if price >= last_notified_price + STEP:
                msg = (
                    f"🚀 ETH виріс до ${price:.2f} "
                    f"(+${price - last_notified_price:.2f} від останнього сигналу)"
                )
                await application.bot.send_message(chat_id=CHAT_ID, text=msg)
                last_notified_price = price

            # Якщо ціна впала на 60 USD або більше
            elif price <= last_notified_price - 60:
                msg = (
                    f"⚠️ ETH впав до ${price:.2f} "
                    f"(-${last_notified_price - price:.2f} від останнього сигналу)"
                )
                await application.bot.send_message(chat_id=CHAT_ID, text=msg)
                last_notified_price = price

        except Exception as e:
            print(f"[ERROR] {e}")

        await asyncio.sleep(60)

# === Запуск Telegram-бота ===
async def start_telegram_bot():
    app_builder = ApplicationBuilder().token(TELEGRAM_TOKEN)
    application = app_builder.build()

    # Команди
    pattern = re.compile(r'^!?status$', re.IGNORECASE)
    application.add_handler(CommandHandler("status", send_status))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(pattern), send_status))

    # Моніторинг ціни — окремим таском
    asyncio.create_task(monitor_price(application))

    print("✅ Бот запущено і працює 24/7")
    # Запускаємо polling і чекаємо закінчення
    await application.run_polling()

# === Головний блок запуску ===
if __name__ == "__main__":
    # Flask у фоновому потоці (daemon=True щоб не блокував вихід)
    threading.Thread(target=run_flask, daemon=True).start()

    # Запускаємо асинхронний Telegram-бот
    asyncio.run(start_telegram_bot())

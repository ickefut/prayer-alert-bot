import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from class_mumin import Mumin

TOKEN = open('Token.txt', 'r').read().strip()

user_data = {}
tasks = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Lütfen yaşadığınız şehri ve ilçeyi girin. (Örnek: Ankara, Çankaya)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message_text = update.message.text.strip()
    
    try:
        sehir, ilce = map(str.strip, message_text.split(",")[:2])
    except ValueError:
        await update.message.reply_text("Lütfen geçerli bir format kullanın: Şehir, İlçe")
        return

    mumin_instance = Mumin(sehir=sehir, ilce=ilce)
    
    if user_id in tasks:
        tasks[user_id].cancel()

    await mumin_instance.get_prayer_times()
    await mumin_instance.read_prayer_times()

    tasks[user_id] = asyncio.create_task(mumin_instance.calc_time(update, context))
    await update.message.reply_text("Namaz vakti bildirimi ayarlandı.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()


import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

# مراحل المحادثة
(ARRIVAL_DATE, PURPOSE, FLIGHT_ARRIVAL, FLIGHT_DEPARTURE, HOTEL) = range(5)
user_data = {}

# Flask لفحص البوت في Render
app = Flask(__name__)
@app.route('/')
def health():
    return 'OK', 200

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# دوال المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! سأساعدك في تعبئة كرت الوصول لتايلاند.\n\n📅 ما هو تاريخ الوصول؟ (مثال: 2025-10-01)")
    return ARRIVAL_DATE

async def get_arrival_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'arrival_date': update.message.text}
    buttons = [
        [InlineKeyboardButton("🎒 سياحة", callback_data="HOLIDAY")],
        [InlineKeyboardButton("💼 عمل", callback_data="BUSINESS")]
    ]
    await update.message.reply_text("🎯 ما هو الغرض من السفر؟", reply_markup=InlineKeyboardMarkup(buttons))
    return PURPOSE

async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['purpose'] = query.data
    await query.edit_message_text("✈️ ما هو رقم رحلة الوصول؟ (مثال: EK384)")
    return FLIGHT_ARRIVAL

async def get_flight_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['flight_arrival'] = update.message.text
    await update.message.reply_text("🛫 ما هو رقم رحلة المغادرة؟ (مثال: EK385)")
    return FLIGHT_DEPARTURE

async def get_flight_departure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['flight_departure'] = update.message.text
    await update.message.reply_text("🏨 ما هو اسم الفندق أو مكان الإقامة في تايلاند؟")
    return HOTEL

async def get_hotel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid]['hotel'] = update.message.text
    data = user_data[uid]
    hotel_clean = data['hotel'].replace(' ', '+')
    url = (
        "https://tdac.immigration.go.th/arrival-card/#/home?"
        f"arrivalDate={data['arrival_date']}&"
        f"purpose={data['purpose']}&"
        f"flightNoArrival={data['flight_arrival']}&"
        f"flightNoDeparture={data['flight_departure']}&"
        f"accommodation={hotel_clean}"
    )
    await update.message.reply_text(f"✅ تم تجهيز بياناتك!\nاضغط هنا لتعبئة كرت الوصول تلقائيًا:\n\n{url}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 تم إلغاء العملية.")
    return ConversationHandler.END

# تشغيل البوت
if __name__ == '__main__':
    token = "7967576252:AAGwbAnJ-KKv-Fjz6Ia5y-jNhZ2JVhJfsVc"

    Thread(target=run).start()

    app_bot = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ARRIVAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_arrival_date)],
            PURPOSE: [CallbackQueryHandler(get_purpose)],
            FLIGHT_ARRIVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flight_arrival)],
            FLIGHT_DEPARTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flight_departure)],
            HOTEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hotel)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app_bot.add_handler(conv)
    app_bot.run_polling()

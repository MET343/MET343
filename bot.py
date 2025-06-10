import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

# مراحل المحادثة
(ARRIVAL_DATE, PURPOSE, FLIGHT_ARRIVAL, FLIGHT_DEPARTURE, HOTEL, CONFIRM) = range(6)
user_data = {}

# فحص البوت في Render
app = Flask(__name__)
@app.route('/')
def health():
    return 'OK', 200

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ مرحباً بك في مساعد كرت الوصول لتايلاند 🇹🇭\n\n"
        "📌 سأرشدك خطوة بخطوة لتعبئة البيانات بالطريقة الصحيحة.\n"
        "ابدأ بإدخال **تاريخ الوصول** (مثال: 2025-10-01)"
    )
    return ARRIVAL_DATE

async def get_arrival_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'arrival_date': update.message.text}
    buttons = [
        [InlineKeyboardButton("🎒 سياحة (Holiday)", callback_data="HOLIDAY")],
        [InlineKeyboardButton("💼 عمل (Business)", callback_data="BUSINESS")]
    ]
    await update.message.reply_text(
        "🎯 ما هو **غرض السفر**؟\n"
        "اختر أحد الخيارات التالية:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return PURPOSE

async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['purpose'] = query.data
    await query.edit_message_text(
        "✈️ أدخل رقم **رحلة الوصول** بدقة كما هو في التذكرة (مثال: EK384)"
    )
    return FLIGHT_ARRIVAL

async def get_flight_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['flight_arrival'] = update.message.text
    await update.message.reply_text(
        "🛫 أدخل رقم **رحلة المغادرة** من تايلاند (مثال: EK385)"
    )
    return FLIGHT_DEPARTURE

async def get_flight_departure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['flight_departure'] = update.message.text
    await update.message.reply_text(
        "🏨 ما هو **عنوان الفندق** أو مكان الإقامة؟\n\n"
        "📍 ملاحظة: انسخ العنوان مباشرة من Google Maps\n"
        "مثال: 222 Ratchaprarop Rd, Bangkok 10400\n"
        "✅ يجب أن يحتوي العنوان على: الشارع، المدينة، الرمز البريدي"
    )
    return HOTEL

async def get_hotel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid]['hotel'] = update.message.text

    data = user_data[uid]
    hotel_clean = data['hotel'].replace(' ', '+')
    tdac_url = (
        "https://tdac.immigration.go.th/arrival-card/#/home?"
        f"arrivalDate={data['arrival_date']}&"
        f"purpose={data['purpose']}&"
        f"flightNoArrival={data['flight_arrival']}&"
        f"flightNoDeparture={data['flight_departure']}&"
        f"accommodation={hotel_clean}"
    )

    await update.message.reply_text(
        "✅ تم تجهيز بياناتك بنجاح!\n\n"
        f"🔗 اضغط هنا لفتح الموقع وتعبئة الكرت تلقائيًا:\n{tdac_url}\n\n"
        "📌 تأكد من اختيار:\n"
        "- Mode of Transport: **Commercial Flight**\n"
        "- Purpose of Travel: **Holiday** (إذا كانت سياحة)\n"
        "- انسخ عنوان الفندق بالكامل من Google Maps\n"
        "- أدخل بريدك الإلكتروني في النهاية للحصول على نسخة PDF\n\n"
        "🧳 رحلتك إلى تايلاند بخير وسلامة ❤️"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 تم إلغاء العملية.")
    return ConversationHandler.END

# تشغيل البوت
if __name__ == '__main__':
    token = os.getenv("BOT_TOKEN") or "7967576252:AAGwbAnJ-KKv-Fjz6Ia5y-jNhZ2JVhJfsVc"
    if not token:
        print("❌ BOT_TOKEN غير موجود")
        exit(1)

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

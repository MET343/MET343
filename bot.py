import os
from flask import Flask
from threading import Thread
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# مراحل المحادثة
(
    ARRIVAL_DATE, NATIONALITY, PURPOSE, FLIGHT_MODE,
    FLIGHT_TYPE, FLIGHT_NO, HOTEL_ADDRESS, DONE
) = range(8)

user_data = {}

# واجهة صحية لـ Render
app = Flask(__name__)
@app.route('/')
def health():
    return 'OK', 200

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# بداية البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ أهلاً بك! سأساعدك على فهم طريقة تعبئة كرت الوصول إلى تايلاند خطوة بخطوة.\n\n"
        "📅 أولاً، ما هو **تاريخ الوصول؟**\nاكتبه بهذا الشكل: 2025-10-01"
    )
    return ARRIVAL_DATE

async def get_arrival_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'arrival_date': update.message.text}
    buttons = [
        [InlineKeyboardButton("🇸🇦 السعودية", callback_data="SAUDI ARABIA")],
        [InlineKeyboardButton("🇦🇪 الإمارات", callback_data="UNITED ARAB EMIRATES")],
    ]
    await update.message.reply_text(
        "🌍 اختر جنسيتك (Nationality):", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return NATIONALITY

async def get_nationality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['nationality'] = query.data
    buttons = [
        [InlineKeyboardButton("🎒 سياحة (Holiday)", callback_data="HOLIDAY")],
        [InlineKeyboardButton("💼 عمل (Business)", callback_data="BUSINESS")],
    ]
    await query.edit_message_text(
        "🎯 ما هو **الغرض من السفر؟**", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return PURPOSE

async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['purpose'] = query.data
    buttons = [
        [InlineKeyboardButton("🛬 جو (AIR)", callback_data="AIR")],
        [InlineKeyboardButton("🚗 بر (LAND)", callback_data="LAND")],
        [InlineKeyboardButton("🚢 بحر (SEA)", callback_data="SEA")],
    ]
    await query.edit_message_text(
        "🚗 اختر **وسيلة الوصول إلى تايلاند (Mode of Travel):**", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return FLIGHT_MODE

async def get_flight_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['flight_mode'] = query.data
    buttons = [
        [InlineKeyboardButton("✈️ طيران تجاري (COMMERCIAL FLIGHT)", callback_data="COMMERCIAL FLIGHT")],
        [InlineKeyboardButton("🚗 سيارة خاصة / أخرى", callback_data="OTHER")],
    ]
    await query.edit_message_text(
        "✈️ حدد **نوع وسيلة النقل:**\nإذا كنت قادمًا عبر رحلة عادية من الخطوط، اختر *طيران تجاري*.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return FLIGHT_TYPE

async def get_flight_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['flight_type'] = query.data
    await query.edit_message_text("🔢 اكتب رقم الرحلة (مثال: EK384):")
    return FLIGHT_NO

async def get_flight_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['flight_no'] = update.message.text
    await update.message.reply_text(
        "🏨 ما هو **عنوان الفندق أو مكان الإقامة في تايلاند؟**\n"
        "💡 مثال: 222 Ratchaprarop Rd, Makkasan, Ratchathewi, Bangkok 10400"
    )
    return HOTEL_ADDRESS

async def get_hotel_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid]['hotel'] = update.message.text
    data = user_data[uid]

    summary = (
        "✅ تم تجهيز بياناتك:\n\n"
        f"📅 تاريخ الوصول: {data['arrival_date']}\n"
        f"🌍 الجنسية: {data['nationality']}\n"
        f"🎯 الغرض: {data['purpose']}\n"
        f"🚗 وسيلة السفر: {data['flight_mode']} ({data['flight_type']})\n"
        f"✈️ رقم الرحلة: {data['flight_no']}\n"
        f"🏨 العنوان في تايلاند:\n{data['hotel']}\n\n"
        "🌐 الآن، يمكنك التوجه للموقع الرسمي وإدخال هذه المعلومات بسهولة:\n"
        "🔗 https://tdac.immigration.go.th"
    )
    await update.message.reply_text(summary)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 تم إلغاء العملية.")
    return ConversationHandler.END

# تشغيل البوت
if __name__ == '__main__':
    BOT_TOKEN = "7967576252:AAGwbAnJ-KKv-Fjz6Ia5y-jNhZ2JVhJfsVc"  # ← حط توكنك هنا
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN مفقود")
        exit(1)

    Thread(target=run).start()

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ARRIVAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_arrival_date)],
            NATIONALITY: [CallbackQueryHandler(get_nationality)],
            PURPOSE: [CallbackQueryHandler(get_purpose)],
            FLIGHT_MODE: [CallbackQueryHandler(get_flight_mode)],
            FLIGHT_TYPE: [CallbackQueryHandler(get_flight_type)],
            FLIGHT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flight_no)],
            HOTEL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hotel_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app_bot.add_handler(conv)
    app_bot.run_polling()

✅ تعليمات رفع البوت على Render:

1. أدخل على https://render.com
2. اختر New > Web Service
3. اربط مستودع GitHub فيه هذا المجلد أو ارفعه من جهازك.
4. في إعدادات الخدمة:
   - Type: Background Worker ✅
   - Build Command: pip install -r requirements.txt
   - Start Command: python bot.py
5. عدّل التوكن داخل ملف bot.py مكان YOUR_BOT_TOKEN_HERE

لا تنس حفظ التغييرات وبدء النشر.

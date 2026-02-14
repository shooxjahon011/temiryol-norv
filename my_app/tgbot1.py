import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. LOYIHA YO'LINI AVTOMATIK SOZLASH
# Bu qism 'my_project' modulini topa olmaslik xatosini yo'qotadi
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # my_app papkasi
BASE_DIR = os.path.dirname(CURRENT_DIR)  # Django_dars (asosiy papka)
sys.path.append(BASE_DIR)

# 2. DJANGO SOZLAMALARI
# 'my_project' nomi settings.py turgan papka nomi bilan bir xil bo'lishi shart
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

# 3. MODELLARNI IMPORT QILISH (django.setup() dan keyin bo'lishi shart)
from my_app.models import UserProfile
import telebot
from telebot import types

# Bot ma'lumotlari
TOKEN = "7833987841:AAE6GjAu_w8AAP97ZMmbzAy7x5y9dLa7ymM"
ADMIN_ID = "8513245980"
bot = telebot.TeleBot(TOKEN)

print("Bot ishga tushdi...")


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn = types.KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "Assalomu alaykum! Ro'yxatdan o'tgan raqamingizni yuboring:", reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    raw_phone = str(message.contact.phone_number).replace("+", "")
    short_phone = raw_phone[-9:]  # Oxirgi 9 ta raqam (901234567)

    user = UserProfile.objects.filter(phone__contains=short_phone).first()

    if user:
        bot.send_message(message.chat.id, f"✅ Sizni topdim, {user.full_name}!\nEndi to'lov chekini (rasm) yuboring.",
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "❌ Siz hali saytda ro'yxatdan o'tmabsiz yoki raqamingiz mos kelmadi.")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    markup = types.InlineKeyboardMarkup()
    # Callback ma'lumotiga foydalanuvchining TG_ID sini biriktiramiz
    btn_accept = types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{message.chat.id}")
    btn_reject = types.InlineKeyboardButton("❌ Rad etish", callback_data=f"no_{message.chat.id}")
    markup.add(btn_accept, btn_reject)

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
                   caption=f"🔔 Yangi to'lov cheki!\n👤 Kimdan: {message.from_user.first_name}\n🆔 TG-ID: {message.chat.id}",
                   reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data.split("_")
    cmd = data[0]

    # "ok" va "no" buyruqlari uchun ikkinchi qiymat bu foydalanuvchining Telegram ID si
    # "del" va "act" buyruqlari uchun esa bazadagi User ID si
    target_id = data[1]

    if cmd == "ok":
        # Bazadagi shu telefon raqami bilan bog'langan oxirgi nofaol foydalanuvchini topish
        # (Yaxshisi telefon raqam orqali qidirish, lekin hozircha oxirgisini olamiz)
        user = UserProfile.objects.filter(is_active=False).last()

        if user:
            code = str(random.randint(1000, 9999))
            user.activation_code = code
            user.is_active = True
            user.activated_at = timezone.now()
            user.save()

            # Adminga boshqaruv tugmasini chiqaramiz
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔴 Faolsizlantirish", callback_data=f"del_{user.id}_{target_id}"))

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"✅ TASDIQLANDI\n👤 User: {user.full_name}\n🔑 Kod: {code}",
                reply_markup=m
            )

            bot.send_message(target_id, f"✅ To'lovingiz tasdiqlandi!\n🔑 Yangi kodingiz: {code}")

    elif cmd == "no":
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                 caption="❌ Rad etildi.")
        bot.send_message(target_id, "❌ To'lov cheki qabul qilinmadi.")

    elif cmd == "del":
        # Admin faolsizlantirishni bossa
        user = UserProfile.objects.filter(id=target_id).first()
        if user:
            user.is_active = False
            user.save()

            # Endi adminga "Qayta faollashtirish" tugmasini chiqaramiz
            m = types.InlineKeyboardMarkup()
            # Uchinchi parametr sifatida foydalanuvchining TG ID sini ham saqlab o'tamiz (xabar yuborish uchun)
            tg_id = data[2] if len(data) > 2 else ""
            m.add(types.InlineKeyboardButton("🟢 Qayta faollashtirish", callback_data=f"act_{user.id}_{tg_id}"))

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"🔴 {user.full_name} FAOLSIZLANTIRILDI.",
                reply_markup=m
            )
            # Foydalanuvchiga xabar
            if tg_id:
                bot.send_message(tg_id, "⚠️ Sizning profilingiz muddati tugadi yoki admin tomonidan to'xtatildi.")

    elif cmd == "act":
        # Admin qayta faollashtirishni bossa
        user = UserProfile.objects.filter(id=target_id).first()
        if user:
            user.is_active = True
            user.activated_at = timezone.now()
            user.save()

            m = types.InlineKeyboardMarkup()
            tg_id = data[2] if len(data) > 2 else ""
            m.add(types.InlineKeyboardButton("🔴 Faolsizlantirish", callback_data=f"del_{user.id}_{tg_id}"))

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"🟢 {user.full_name} QAYTA FAOLLASHTIRILDI.",
                reply_markup=m
            )
            if tg_id:
                bot.send_message(tg_id, "✅ Profilingiz qayta faollashtirildi! Endi kirishingiz mumkin.")


bot.polling(none_stop=True)
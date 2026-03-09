import uuid
import time
import os
from telebot import types
from core.db import db
from bot.keyboards import premium_inline_keyboard

def handle_premium_menu(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        return

    points = user['points']
    status = db.get_premium_status(user_id)
    
    until_date = "Yo‘q"
    if status['until']:
        until_date = status['until'][:10]
        
    status_text = "❌ Yo‘q"
    if status['active']:
        if status['type'] == 'trial':
            status_text = "🎁 Sinov muddati"
        elif status['type'] == 'subscription':
            status_text = "✅ Obuna (Avto-yangilanish)"
        else:
            status_text = "✅ Premium Faol"
    
    plan_type = user.get('plan_type', 'free').capitalize()
    if plan_type == 'Vip': plan_type = 'VIP'
    
    # Use yasha_points if available and non-zero, else points
    # This ensures backward compatibility until migration is complete
    raw_yasha = user.get('yasha_points', 0)
    raw_points = user.get('points', 0)
    yasha_points = raw_yasha if raw_yasha > 0 else raw_points

    text = (
        "💳 <b>Obuna bo'limi</b>\n"
        f"- Tarifingiz: {plan_type}\n"
        f"- Tugash sanasi: {until_date}\n"
        f"- Yasha coinlaringiz: {yasha_points}\n\n"
        "👇 <b>Quyidagi menyudan kerakli bo'limni tanlang:</b>"
    )
    
    markup = premium_inline_keyboard()
    # If trial active, maybe show "Buy to extend"
    # If expired, show "Buy"
    
    with open("assets/premium.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=text, reply_markup=markup, parse_mode="HTML")

def handle_premium_info(message, bot):
    text = (
        "<b>💎 PREMIUM — 49 000 so‘m / oy</b>\n\n"
        "✅ AI Menyu — oyiga 1 marta (7 kunlik)\n"
        "✅ AI Mashqlar rejasi — oyiga 1 marta\n"
        "⚠️ Kaloriya tahlili — kuniga 3 marta\n"
        "⚠️ AI Chat (savol-javob) — kuniga 3 marta\n\n"
        
        "<b>👑 VIP — 97 000 so‘m / oy</b>\n\n"
        "✅ AI Menyu — oyiga 4 marta (28 kunlik)\n"
        "✅ Cheksiz kaloriya tahlili\n"
        "✅ Cheksiz AI Chat\n"
        "✅ Cheksiz retseptlar\n\n"
        "<b>O'zingizga qulay tarifni tanlang👇🏻</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💎 PREMIUM (49.000)", callback_data="select_premium"))
    markup.add(types.InlineKeyboardButton("👑 VIP (97.000)", callback_data="select_vip"))
    markup.add(types.InlineKeyboardButton("📄 Ommaviy oferta", callback_data="premium_offer"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

def handle_premium_info_detailed(message, bot):
    text = (
        "Bu yerda YASHA sizga qanchalik kuchli yordam berishini tanlaysiz. <b>Har bir tarif — boshqa daraja.</b>\n\n"
        "<b>💎 PREMIUM — 49 000 so‘m / oy</b>\n\n"
        "👉 Boshlash va tartibga tushish uchun ideal\n\n"
        "Agar siz sog‘lom hayotni asta-sekin boshlamoqchi bo‘lsangiz — shu tarif yetarli.\n\n"
        "<b>Nimalar kiradi:</b>\n"
        "\t- ✅ AI Menyu — oyiga 1 marta (7 kunlik)\n"
        "→ Vazningiz va maqsadingizga mos ovqatlanish rejasi\n"
        "\t- ✅ AI Mashqlar — oyiga 1 marta\n"
        "→ Uyda yoki zalda bajariladigan mashqlar\n"
        "\t- ⚠️ Kaloriya tahlili — kuniga 3 marta\n"
        "→ Nima yeyayotganingiz nazorat ostida\n"
        "\t- ⚠️ AI Chat — kuniga 3 savol\n"
        "→ Savollar cheklangan\n\n"
        "<b>🔎 Kimlar uchun?</b>\n"
        "Yangi boshlayotganlar va rejaga kirib olishni xohlaydiganlar.\n\n"
        
        "<b>👑 VIP — 97 000 so‘m / oy</b>\n\n"
        "👉 Natija, tezlik va to‘liq nazorat uchun\n\n"
        "Bu tarif — o‘zingizga real sarmoya. Hech qanday cheklovsiz.\n\n"
        "<b>Nimalar kiradi:</b>\n"
        "\t- 🔥 AI Menyu — oyiga 4 marta (28 kunlik)\n"
        "→ Deyarli har hafta yangilanadi\n"
        "\t- 🔥 Cheksiz kaloriya tahlili\n"
        "→ Istagancha surat yuboring\n"
        "\t- 🔥 Cheksiz AI Chat\n"
        "→ Savolingiz tugamaydi\n"
        "\t- 🔥 Cheksiz AI Retseptlar\n"
        "→ Uyda bor mahsulotlardan mos ovqat\n\n"
        "<b>🚀 Kimlar uchun?</b>\n"
        "Tez natija xohlaydiganlar, ozish yoki formaga kirishni jiddiy olganlar.\n\n"
        "⚖️ Qisqa taqqoslash\n"
        "\t- <b>PREMIUM</b> — boshlash uchun\n"
        "\t- <b>VIP</b> — maksimal natija uchun\n\n"
        "<b>💳 To‘lov turlari:</b> Click · Payme · Uzum"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💎 PREMIUM (49.000)", callback_data="select_premium"))
    markup.add(types.InlineKeyboardButton("👑 VIP (97.000)", callback_data="select_vip"))
    markup.add(types.InlineKeyboardButton("📄 Ommaviy oferta", callback_data="premium_offer"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

def handle_offer_download(message, bot):
    try:
        with open("assets/offerta.pdf", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption="📄 **Ommaviy oferta**", parse_mode="Markdown")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "⚠️ Hozircha fayl yuklanmagan.")

def handle_premium_buy(message, bot):
    # This invokes the Simplified version (Original handle_premium_info)
    handle_premium_info(message, bot)
from core.config import ADMIN_IDS, PRICE_1_MONTH, PRICE_3_MONTHS

# Payment details (Mock)
PAYMENT_CARDS = {
    "click": "8600 0000 0000 0000 (Click)",
    "payme": "9860 0000 0000 0000 (Payme)",
    "uzum": "4400 0000 0000 0000 (Uzum)"
}



def register_handlers(bot):
    # Free redemption option removed - premium now requires payment only
    # @bot.callback_query_handler(func=lambda call: call.data in ["redeem_7"])
    # def handle_redemption(call):
    #     ... (removed)

    @bot.callback_query_handler(func=lambda call: call.data in ["select_premium", "select_vip"])
    def handle_plan_selection(call):
        provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
        
        if not provider_token:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "⚠️ <b>To'lov tizimi hozircha sozlanmagan.</b>\n\n"
                "Iltimos, admin bilan bog'laning yoki keyinroq urinib ko'ring.\n\n"
                "📞 Qayta aloqa: @admin",
                parse_mode="HTML"
            )
            return
        
        days = 30
        
        if call.data == "select_premium":
            amount = 4900000 # 49 000 UZS
            plan_name = "premium"
            title = "Fitness Bot Premium (1 oy)"
        else:
            amount = 9700000 # 97 000 UZS
            plan_name = "vip"
            title = "Fitness Bot VIP (1 oy)"
            
        # Format for display (e.g. 49 000)
        price_display = f"{amount // 100:,}".replace(",", " ")
        
        description = f"{title}. Narxi: {price_display} so'm"
        payload = f"{plan_name}_{days}" # e.g. premium_30
        currency = "UZS"
        prices = [types.LabeledPrice(label=title, amount=amount)]

        bot.send_invoice(
            call.message.chat.id,
            title=title,
            description=description,
            invoice_payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter="premium-sub",
            is_flexible=False
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        user_id = message.from_user.id
        payment = message.successful_payment
        payload = payment.invoice_payload # e.g., premium_30
        
        parts = payload.split("_")
        plan_type = parts[0]
        days = int(parts[1])
        
        amount = payment.total_amount / 100 # Convert back to UZS
        currency = payment.currency
        
        # Create order record
        order_id = f"pay_{payment.provider_payment_charge_id}"
        db.create_order(order_id, user_id, days, amount, currency)
        db.update_order_status(order_id, 'paid')
        
        # Activate Plan
        db.set_user_plan(user_id, plan_type, days)
        
        # Set Auto-Renew flag
        db.update_user_profile(user_id, auto_renew=True)
        
        bot.send_message(user_id, f"✅ <b>To'lov muvaffaqiyatli amalga oshirildi!</b>\n\nSizga {days} kunlik <b>{plan_type.upper()}</b> obuna faollashtirildi. 🎉\nBarcha imkoniyatlardan foydalanishingiz mumkin!", parse_mode="HTML")
        
        # Notify Admins
        for admin_id in ADMIN_IDS:
            if admin_id:
                try:
                    bot.send_message(admin_id, f"💰 **Yangi To'lov!**\nUser: {message.from_user.first_name} (ID: {user_id})\nSumma: {amount} {currency}\nTarif: {days} kun")
                except Exception:
                    pass

    @bot.callback_query_handler(func=lambda call: call.data == "back_premium")
    def back_to_premium(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_premium_menu(call.message, bot)

    # Admin manual confirm kept just in case
    @bot.message_handler(commands=['confirm_premium'])
    def admin_confirm_premium(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        try:
            parts = message.text.split()
            order_id = parts[1]
            days = int(parts[2])
            
            order = db.get_order(order_id)
            if not order:
                bot.reply_to(message, "❌ Buyurtma topilmadi.")
                return
            
            db.update_order_status(order_id, 'paid')
            db.set_premium(order['user_id'], days)
            
            bot.reply_to(message, f"✅ To'lov tasdiqlandi! User {order['user_id']} ga {days} kun Premium berildi.")
        except Exception:
            pass

def require_premium(func):
    """Decorator to restrict handlers to premium users only"""
    def wrapper(message, bot, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id is None:
            user_id = message.from_user.id
            
        if not db.is_premium(user_id):
            # Upsell message
            text = (
                "💎 **Premium kerak**\n\n"
                "Bu xizmat faqat Premium foydalanuvchilar uchun.\n"
                "Sizning sinov muddatingiz tugagan.\n\n"
                "Premium ochish uchun “💎 Premium” bo‘limiga o‘ting."
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💎 Premium olish", callback_data="premium_buy"))
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
            return
        return func(message, bot, *args, **kwargs)
    return wrapper

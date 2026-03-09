import uuid
import time
import os
from telebot import types
from core.db import db
from bot.keyboards import premium_inline_keyboard
from bot.languages import get_text

def handle_premium_menu(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        return

    points = user['points']
    status = db.get_premium_status(user_id)
    lang = user.get('language', 'uz')
    
    until_date = get_text("status_no", lang)
    if status['until']:
        until_date = status['until'][:10]
        
    status_text = get_text("status_no", lang)
    if status['active']:
        if status['type'] == 'trial':
            status_text = get_text("status_trial", lang)
        elif status['type'] == 'subscription':
            status_text = get_text("status_sub", lang)
        else:
            status_text = get_text("status_active", lang)
    
    plan_type = user.get('plan_type', 'free').capitalize()
    if plan_type == 'Vip': plan_type = 'VIP'
    
    # Use yasha_points if available and non-zero, else points
    # This ensures backward compatibility until migration is complete
    raw_yasha = user.get('yasha_points', 0)
    raw_points = user.get('points', 0)
    yasha_points = raw_yasha if raw_yasha > 0 else raw_points
    
    # Construct text using keys
    title = get_text("premium_menu_title", lang)
    t_plan = get_text("premium_menu_plan", lang, plan=plan_type)
    t_until = get_text("premium_menu_until", lang, date=until_date)
    t_points = get_text("premium_menu_points", lang, points=yasha_points)
    t_footer = get_text("premium_menu_footer", lang)

    text = (
        f"{title}\n"
        f"{t_plan}\n"
        f"{t_until}\n"
        f"{t_points}\n\n"
        f"{t_footer}"
    )
    
    markup = premium_inline_keyboard(lang=lang)
    # If trial active, maybe show "Buy to extend"
    # If expired, show "Buy"
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")

def handle_premium_info(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    text = get_text("premium_sales_short", lang)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text("btn_buy_premium", lang), callback_data="select_premium"))
    markup.add(types.InlineKeyboardButton(get_text("btn_buy_vip", lang), callback_data="select_vip"))
    markup.add(types.InlineKeyboardButton(get_text("btn_offer", lang), callback_data="premium_offer"))
    
    try:
        with open("bot/assets/plans_table.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

def handle_premium_info_detailed(message, bot):
    # Redirect to standard info for now to ensure localization is clean
    # or use same text.
    handle_premium_info(message, bot)

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

    @bot.callback_query_handler(func=lambda call: call.data in ["pay_plus_1", "pay_vip_1", "pay_plus_3", "pay_vip_3"])
    def handle_plan_selection(call):
        from core.config import PRICE_1_MONTH, PRICE_VIP_1_MONTH, PRICE_3_MONTHS, PRICE_VIP_3_MONTHS

        provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
        
        if not provider_token:
            bot.answer_callback_query(call.id, "⚠️ To'lov tizimi vaqtincha ishlamayapti.")
            return
            
        data = call.data
        days = 30
        title_key = "invoice_title_premium"
        plan_code = "premium"
        
        # Determine Amount and Plan
        amount = PRICE_1_MONTH # Default
        
        if "vip" in data:
            plan_code = "vip"
            title_key = "invoice_title_vip"
            
        if "3" in data:
            days = 90
            # 3 month prices
            if plan_code == "premium": amount = PRICE_3_MONTHS
            else: amount = PRICE_VIP_3_MONTHS
        else:
            # 1 month prices
            if plan_code == "premium": amount = PRICE_1_MONTH
            else: amount = PRICE_VIP_1_MONTH
            
        price_display = f"{amount // 100:,}".replace(",", " ")
        lang = db.get_user_language(call.from_user.id)
        title = get_text(title_key, lang)
        if days == 90: title += " (3 oy)"
        
        description = get_text("invoice_desc", lang, title=title, price=price_display)
        payload = f"{plan_code}_{days}" 
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
        
        lang = db.get_user_language(user_id)
        msg_title = get_text("payment_success_title", lang)
        msg_desc = get_text("payment_success_desc", lang, days=days, plan=plan_type.upper())
        
        bot.send_message(user_id, f"{msg_title}\n\n{msg_desc}", parse_mode="HTML")
        
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
            lang = db.get_user_language(user_id)
            text = get_text("premium_required_upsell", lang)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("btn_get_premium", lang), callback_data="premium_buy"))
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
            return
        return func(message, bot, *args, **kwargs)
    return wrapper

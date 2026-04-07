"""
💍 СВАДЕБНЫЙ ТЕЛЕГРАМ-БОТ
==========================
Установка и запуск:
1. pip install pyTelegramBotAPI
2. Замените BOT_TOKEN на токен от @BotFather
3. Замените ADMIN_CHAT_ID на ваш Telegram ID (узнать у @userinfobot)
4. python wedding_bot.py
"""

import telebot
from telebot import types
import json
import os
from datetime import datetime

# ==================== НАСТРОЙКИ ====================

BOT_TOKEN = "8689445544:AAFoyL3PwpLrcHquWr-xYLqUoVBbSzoDnhI"

ADMIN_CHAT_ID = 8130924217  # Ваш Telegram ID

# Данные о свадьбе — меняйте под себя!
WEDDING = {
    "groom": "Егор",
    "bride": "Света",
    "date": "16 мая",
    "zags_time": "14:00",
    "zags_address": "ул. Советская, 47",
    "banquet_time": "15:30",
    "banquet_place": "ул. Советская, 47",
    "banquet_address": "ул. Советская, 47",
    "dresscode": "Мужчины: белый верх, чёрный низ. Девушки: пастельные тона — зелёный, жёлтый, синий",
}

DRINKS = [
    "🍷 Красное вино",
    "🥂 Шампанское",
    "🍸 Виски",
    "🍺 Пиво",
    "🍹 Коктейли",
    "🧃 Без алкоголя",
]

# =====================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояний пользователей (в памяти)
user_data = {}

RESPONSES_FILE = "wedding_responses.json"


def load_responses():
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_response(data):
    responses = load_responses()
    responses.append(data)
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)


def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"step": 0, "drinks": [], "attendance": "", "names": "", "ceremony": ""}
    return user_data[uid]


# ==================== ШАГ 1: ПРИВЕТСТВИЕ ====================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    uid = message.from_user.id
    user_data[uid] = {"step": 1, "drinks": [], "attendance": "", "names": "", "ceremony": ""}

    w = WEDDING
    text = (
        f"💍 *{w['groom']} & {w['bride']} приглашают вас на свадьбу!*\n\n"
        f"📅 Дата: *{w['date']}*\n"
        f"⛪ Загс: *{w['zags_time']}*, {w['zags_address']}\n"
        f"🍽 Банкет: *{w['banquet_time']}*, {w['banquet_place']}\n"
        f"📍 Адрес банкета: {w['banquet_address']}\n"
        f"👗 Дресскод: _{w['dresscode']}_\n\n"
        f"Пожалуйста, подтвердите своё участие:"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🥂 Буду один(а)", callback_data="attend_solo"),
        types.InlineKeyboardButton("👫 Буду с партнёром", callback_data="attend_pair"),
        types.InlineKeyboardButton("😔 К сожалению, не смогу", callback_data="attend_no"),
    )

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


# ==================== ШАГ 1 → обработка кнопок ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("attend_"))
def handle_attendance(call):
    uid = call.from_user.id
    u = get_user(uid)

    bot.answer_callback_query(call.id)

    if call.data == "attend_no":
        u["attendance"] = "Не придёт"
        save_response({
            "telegram_id": uid,
            "username": call.from_user.username,
            "attendance": "Не придёт",
            "timestamp": datetime.now().isoformat(),
        })
        bot.edit_message_text(
            "😢 Жаль, что вы не сможете прийти. Спасибо, что сообщили!\n\nЖелаем всего самого доброго! 💫",
            call.message.chat.id,
            call.message.message_id,
        )
        notify_admin(call.from_user, {"attendance": "Не придёт"})
        return

    u["attendance"] = "Один" if call.data == "attend_solo" else "С партнёром"
    u["step"] = 2

    if call.data == "attend_solo":
        prompt = "Как вас зовут?\n\nВведите своё *Имя и Фамилию*:"
    else:
        prompt = (
            "Отлично! Как вас зовут?\n\n"
            "Введите имена через /\n"
            "_Пример: Алексей Смирнов / Ольга Смирнова_"
        )

    bot.edit_message_text(
        f"✅ Отлично! Ждём вас!\n\n{prompt}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
    )


# ==================== ШАГ 2: ИМЯ ====================

@bot.message_handler(func=lambda m: get_user(m.from_user.id).get("step") == 2)
def handle_name(message):
    uid = message.from_user.id
    u = get_user(uid)
    u["names"] = message.text.strip()
    u["step"] = 3

    # Строим клавиатуру с напитками
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(d, callback_data=f"drink_{i}") for i, d in enumerate(DRINKS)]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="drinks_done"))

    bot.send_message(
        message.chat.id,
        "🥂 *Что будете пить на свадьбе?*\n\nМожно выбрать несколько вариантов, затем нажмите *Готово*:",
        parse_mode="Markdown",
        reply_markup=markup,
    )


# ==================== ШАГ 3: НАПИТКИ ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("drink_") or c.data == "drinks_done")
def handle_drinks(call):
    uid = call.from_user.id
    u = get_user(uid)

    if u.get("step") != 3:
        bot.answer_callback_query(call.id)
        return

    if call.data == "drinks_done":
        if not u["drinks"]:
            bot.answer_callback_query(call.id, "Выберите хотя бы один напиток!")
            return

        bot.answer_callback_query(call.id)
        u["step"] = 4

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⛪ Приеду на церемонию в загс", callback_data="ceremony_yes"),
            types.InlineKeyboardButton("🍽 Приеду сразу на банкет", callback_data="ceremony_no"),
        )

        w = WEDDING
        bot.edit_message_text(
            f"📍 *Планы на день свадьбы*\n\n"
            f"⛪ Загс: *{w['zags_time']}*, {w['zags_address']}\n"
            f"🍽 Банкет: *{w['banquet_time']}*, {w['banquet_place']}\n\n"
            f"Вы придёте на церемонию в загс или сразу на банкет?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )
        return

    # Переключаем напиток
    idx = int(call.data.split("_")[1])
    drink = DRINKS[idx]

    if drink in u["drinks"]:
        u["drinks"].remove(drink)
        bot.answer_callback_query(call.id, f"Убрано: {drink}")
    else:
        u["drinks"].append(drink)
        bot.answer_callback_query(call.id, f"Добавлено: {drink}")

    # Обновляем клавиатуру — отмечаем выбранные
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for i, d in enumerate(DRINKS):
        label = ("✅ " if d in u["drinks"] else "") + d
        buttons.append(types.InlineKeyboardButton(label, callback_data=f"drink_{i}"))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="drinks_done"))

    selected = ", ".join(u["drinks"]) if u["drinks"] else "пока ничего не выбрано"
    bot.edit_message_text(
        f"🥂 *Что будете пить?*\n\nВыбрано: _{selected}_\n\nНажмите *Готово* когда выберете всё:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup,
    )


# ==================== ШАГ 4: ЗАГС ИЛИ БАНКЕТ ====================

@bot.callback_query_handler(func=lambda c: c.data in ["ceremony_yes", "ceremony_no"])
def handle_ceremony(call):
    uid = call.from_user.id
    u = get_user(uid)

    bot.answer_callback_query(call.id)

    u["ceremony"] = "Загс + Банкет" if call.data == "ceremony_yes" else "Только банкет"
    u["step"] = 5

    # Сохраняем ответ
    response = {
        "telegram_id": uid,
        "username": call.from_user.username,
        "first_name": call.from_user.first_name,
        "names": u["names"],
        "attendance": u["attendance"],
        "drinks": u["drinks"],
        "ceremony": u["ceremony"],
        "timestamp": datetime.now().isoformat(),
    }
    save_response(response)
    notify_admin(call.from_user, response)

    # Шаг 5 — итоговое сообщение
    w = WEDDING
    drinks_str = ", ".join(u["drinks"])
    text = (
        f"🎉 *Регистрация завершена! Спасибо!*\n\n"
        f"Ваши данные сохранены. Будем рады вас видеть!\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📋 *Ваш ответ:*\n"
        f"👤 Гость(и): {u['names']}\n"
        f"🥂 Напитки: {drinks_str}\n"
        f"📍 Приедете: {u['ceremony']}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📅 *{w['date']}*\n"
        f"⛪ Загс: *{w['zags_time']}*, {w['zags_address']}\n"
        f"🍽 Банкет: *{w['banquet_time']}*\n"
        f"📍 {w['banquet_place']}, {w['banquet_address']}\n"
        f"👗 Дресскод: _{w['dresscode']}_\n\n"
        f"С нетерпением ждём вас! 💍"
    )

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")


# ==================== УВЕДОМЛЕНИЕ АДМИНИСТРАТОРА ====================

def notify_admin(tg_user, data):
    try:
        drinks_str = ", ".join(data.get("drinks", [])) or "—"
        text = (
            f"🔔 *Новый ответ на свадьбу*\n\n"
            f"👤 Telegram: @{tg_user.username or '—'} (ID: {tg_user.id})\n"
            f"📝 Гость(и): {data.get('names', '—')}\n"
            f"✅ Участие: {data.get('attendance', '—')}\n"
            f"🥂 Напитки: {drinks_str}\n"
            f"📍 Приедет: {data.get('ceremony', '—')}\n"
        )
        bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка уведомления: {e}")


# ==================== КОМАНДА /СПИСОК ====================

@bot.message_handler(commands=["spisok"])
def show_list(message):
    """Только для администратора — показывает всех гостей"""
    if message.from_user.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    responses = load_responses()
    if not responses:
        bot.send_message(message.chat.id, "Пока нет ответов")
        return

    coming = [r for r in responses if r.get("attendance") != "Не придёт"]
    not_coming = [r for r in responses if r.get("attendance") == "Не придёт"]

    text = f"📋 *Список гостей* ({len(coming)} придут, {len(not_coming)} нет)\n\n"
    for r in coming:
        text += f"✅ {r.get('names', '—')} | {r.get('ceremony', '—')}\n"

    if not_coming:
        text += f"\n❌ Не придут:\n"
        for r in not_coming:
            text += f"• @{r.get('username', '—')}\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# ==================== ЗАПУСК ====================

print("🤖 Свадебный бот запущен!")
print(f"📋 Ответы сохраняются в файл: {RESPONSES_FILE}")
print("Остановить: Ctrl+C\n")

bot.infinity_polling()

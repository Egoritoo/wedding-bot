"""
💍 СВАДЕБНЫЙ ТЕЛЕГРАМ-БОТ — Егор & Света
"""

import telebot
from telebot import types
import json
import os
from datetime import datetime

BOT_TOKEN = "8689445544:AAFoyL3PwpLrcHquWr-xYLqUoVBbSzoDnhI"
ADMIN_CHAT_ID = 8130924217

WEDDING = {
    "groom": "Егор",
    "bride": "Света",
    "date": "16 мая",
    "zags_time": "15:00",
    "zags_address": "г. Тула, ул. Советская, 47 (ЗАГС)",
    "banquet_time": "16:30",
    "banquet_place": "Площадка «Воздух»",
    "banquet_address": "с. Высокое, 125 (малая площадка «Воздух»)",
}

DRINKS = [
    "🍾 Вино белое",
    "🍷 Вино красное",
    "🥃 Виски",
    "🥂 Коньяк",
    "🫗 Водка",
    "🧃 Без алкоголя",
]

DRESSCODE_IMAGE = "dresscode.jpg"

bot = telebot.TeleBot(BOT_TOKEN)
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
        result = bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
        print(f"✅ Уведомление отправлено админу, message_id: {result.message_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        # Пробуем без Markdown
        try:
            drinks_str = ", ".join(data.get("drinks", [])) or "—"
            text_plain = (
                f"Новый ответ на свадьбу\n\n"
                f"Гость: {data.get('names', '—')}\n"
                f"Участие: {data.get('attendance', '—')}\n"
                f"Напитки: {drinks_str}\n"
                f"Приедет: {data.get('ceremony', '—')}\n"
            )
            bot.send_message(ADMIN_CHAT_ID, text_plain)
            print("✅ Уведомление отправлено без Markdown")
        except Exception as e2:
            print(f"❌ Повторная ошибка: {e2}")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    uid = message.from_user.id
    user_data[uid] = {"step": 1, "drinks": [], "attendance": "", "names": "", "ceremony": ""}
    print(f"▶️ /start от пользователя {uid} (@{message.from_user.username})")

    # Если это админ — отправляем тестовое уведомление
    if uid == ADMIN_CHAT_ID:
        bot.send_message(uid, "✅ Бот работает! Вы вошли как администратор. Уведомления будут приходить сюда.")

    w = WEDDING
    text = (
        "Привет, дорогой друг! 💛\n\n"
        "Мы будем очень рады видеть тебя (и, конечно, твою вторую половинку) на нашей свадьбе! 🎉\n\n"
        f"💍 *Регистрация брака:*\n{w['zags_time']}, {w['zags_address']}\n\n"
        f"🥂 *Банкет:*\n{w['banquet_time']}, {w['banquet_address']}\n\n"
        "Пожалуйста, заполни небольшую анкету ниже 👇\n"
        "Так ты подтвердишь своё участие и очень поможешь нам всё красиво и удобно организовать ✨\n\n"
        "Ждём тебя с нетерпением! 💕"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🥂 Буду один(а)", callback_data="attend_solo"),
        types.InlineKeyboardButton("👫 Буду с партнёром", callback_data="attend_pair"),
        types.InlineKeyboardButton("😔 К сожалению, не смогу", callback_data="attend_no"),
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=["test"])
def test_notify(message):
    """Команда для проверки уведомлений"""
    if message.from_user.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    try:
        bot.send_message(ADMIN_CHAT_ID, "🔔 Тестовое уведомление — всё работает!")
        bot.send_message(message.chat.id, "✅ Уведомление отправлено себе!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")


@bot.callback_query_handler(func=lambda c: c.data.startswith("attend_"))
def handle_attendance(call):
    uid = call.from_user.id
    u = get_user(uid)
    bot.answer_callback_query(call.id)
    print(f"📌 Выбор участия: {call.data} от {uid}")

    if call.data == "attend_no":
        u["attendance"] = "Не придёт"
        save_response({"telegram_id": uid, "username": call.from_user.username, "attendance": "Не придёт", "timestamp": datetime.now().isoformat()})
        bot.edit_message_text("😢 Жаль, что не получится прийти. Спасибо, что сообщил(а)!\n\nЖелаем всего самого доброго! 💫", call.message.chat.id, call.message.message_id)
        notify_admin(call.from_user, {"attendance": "Не придёт"})
        return

    u["attendance"] = "Один" if call.data == "attend_solo" else "С партнёром"
    u["step"] = 2

    if call.data == "attend_solo":
        prompt = "Как вас зовут? 😊\n\nУкажите своё *имя и фамилию*:"
    else:
        prompt = "Как вас зовут? 😊\n\nУкажите ваше имя и фамилию, а также имя и фамилию вашей второй половинки 💕\n\n_Пример: Алексей Смирнов / Ольга Смирнова_"

    bot.edit_message_text(f"Отлично, ждём тебя! 🎉\n\n{prompt}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")


@bot.message_handler(func=lambda m: get_user(m.from_user.id).get("step") == 2)
def handle_name(message):
    uid = message.from_user.id
    u = get_user(uid)
    u["names"] = message.text.strip()
    u["step"] = 3
    print(f"📝 Имя введено: {u['names']} от {uid}")

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(d, callback_data=f"drink_{i}") for i, d in enumerate(DRINKS)]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="drinks_done"))
    bot.send_message(message.chat.id, "Пора выбрать напитки для отличного настроения 🥂✨\n\nОтметьте всё, что вам нравится (можно несколько):", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("drink_") or c.data == "drinks_done")
def handle_drinks(call):
    uid = call.from_user.id
    u = get_user(uid)

    if u.get("step") != 3:
        bot.answer_callback_query(call.id)
        return

    if call.data == "drinks_done":
        if not u["drinks"]:
            bot.answer_callback_query(call.id, "Выберите хотя бы один вариант!")
            return
        bot.answer_callback_query(call.id)
        u["step"] = 4
        w = WEDDING
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("💍 Приеду на церемонию в ЗАГС", callback_data="ceremony_yes"),
            types.InlineKeyboardButton("🥂 Приеду сразу на банкет", callback_data="ceremony_no"),
        )
        bot.edit_message_text(
            f"Где встретимся? 😊\n\n"
            f"💍 *{w['zags_time']}* — регистрация\n{w['zags_address']}\n\n"
            f"🥂 *{w['banquet_time']}* — банкет\n{w['banquet_address']}\n\n"
            f"На церемонии в ЗАГСе или уже на банкете?",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup,
        )
        return

    idx = int(call.data.split("_")[1])
    drink = DRINKS[idx]
    if drink in u["drinks"]:
        u["drinks"].remove(drink)
        bot.answer_callback_query(call.id, f"Убрано: {drink}")
    else:
        u["drinks"].append(drink)
        bot.answer_callback_query(call.id, f"Добавлено: {drink}")

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(("✅ " if d in u["drinks"] else "") + d, callback_data=f"drink_{i}") for i, d in enumerate(DRINKS)]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="drinks_done"))
    selected = ", ".join(u["drinks"]) if u["drinks"] else "пока ничего не выбрано"
    bot.edit_message_text(f"Пора выбрать напитки 🥂✨\n\nВыбрано: _{selected}_\n\nНажмите *Готово* когда выберете всё:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data in ["ceremony_yes", "ceremony_no"])
def handle_ceremony(call):
    uid = call.from_user.id
    u = get_user(uid)
    bot.answer_callback_query(call.id)

    u["ceremony"] = "ЗАГС + Банкет" if call.data == "ceremony_yes" else "Только банкет"
    u["step"] = 5
    print(f"✅ Анкета завершена: {u['names']}, {u['ceremony']}")

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

    w = WEDDING
    drinks_str = ", ".join(u["drinks"])

    if u["ceremony"] == "ЗАГС + Банкет":
        arrival = f"💍 Ждём тебя в *{w['zags_time']}* на регистрации\n📍 {w['zags_address']}"
    else:
        arrival = f"🥂 Ждём тебя в *{w['banquet_time']}* на банкете\n📍 {w['banquet_address']}"

    text = (
        f"С нетерпением ждём вас! До встречи 💕\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📋 *Ваши данные:*\n"
        f"👤 {u['names']}\n"
        f"🥂 Напитки: {drinks_str}\n"
        f"📍 Приедете: {u['ceremony']}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🗓 *{w['date']}*\n\n"
        f"{arrival}\n\n"
        f"💍 Регистрация: *{w['zags_time']}*, {w['zags_address']}\n"
        f"🥂 Банкет: *{w['banquet_time']}*, {w['banquet_address']}\n\n"
        f"👗 А ниже — напоминание о дресс-коде:"
    )

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    if os.path.exists(DRESSCODE_IMAGE):
        with open(DRESSCODE_IMAGE, "rb") as photo:
            bot.send_photo(call.message.chat.id, photo)
    else:
        bot.send_message(
            call.message.chat.id,
            "👗 *Дресс-код:*\n\n"
            "Для нас самое главное — ваше присутствие!\n\n"
            "👔 *Мужчины:* белый верх (поло, футболка, рубашка), чёрный низ (брюки)\n"
            "👗 *Женщины:* пастельные тона — зелёный, голубой, сиреневый, розовый, жёлтый, персиковый",
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["spisok"])
def show_list(message):
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


print("💍 Свадебный бот Егор & Света запущен!")
print(f"📋 Ответы сохраняются в: {RESPONSES_FILE}")
print("Остановить: Ctrl+C\n")

bot.infinity_polling()

import telebot
import re
import os
import time
from datetime import datetime

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1364254252
ADMIN_PASSWORD = "08091913"

# ⚠️ ВАЖНО! Поставьте дату ВЧЕРАШНЕГО дня (для теста)
# Тогда любой, кто вступил сегодня, будет считаться "новым"
BOT_START_DATE = datetime(2026, 6, 13, 0, 0, 0)  # ← Вчерашняя дата
BOT_ADDED_TIMESTAMP = int(BOT_START_DATE.timestamp())

if not BOT_TOKEN:
    raise ValueError("❌ Не указан BOT_TOKEN!")

print("=" * 50)
print(f"🔄 ЗАПУСК БОТА")
print(f"📅 Порог даты: {BOT_START_DATE.strftime('%d.%m.%Y %H:%M:%S')}")
print(f"🔢 Timestamp порога: {BOT_ADDED_TIMESTAMP}")
print("=" * 50)

# ============================================================
# ЗАПРЕЩЁННЫЕ СЛОВА
# ============================================================
FORBIDDEN_WORDS = [
    "подработка", "заработок", "заработать", "заработнаяплата",
    "удаленнаяработа", "удаленка", "работавинтернете", "работаонлайн",
    "вакансия", "дополнительныйдоход", "свободныйграфик", "легкиеденьги",
    "доходбезвложений", "пассивныйдоход", "работанадому", "заработокбезопыта",
    "ищулюдей", "ищусотрудника", "ищучеловека", "ищуработника",
    "ищукандидата", "ищудевушку", "ищупарня", "ищупомощника",
    "ищуассистента", "требуютсясотрудники", "требуетсясотрудник",
    "набираемсотрудников", "наборсотрудников", "открытавакансия",
    "приглашаювкоманду", "ищемлюдей", "ищемсотрудников", "ищемработников",
    "вакансияоткрыта", "заработнаяплатавысокая",
]

# ============================================================
# ХРАНИЛИЩЕ
# ============================================================
authorized_users = {ADMIN_ID: True}

# ============================================================
# БОТ
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)


# ============================================================
# ОЧИСТКА ТЕКСТА
# ============================================================
def clean_text(text):
    if not text:
        return ""
    original = text
    text = text.lower()
    text = text.replace(" ", "")
    replacements = {
        '@': 'а', '4': 'ч', '0': 'о', '3': 'з',
        'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с',
        'y': 'у', 'k': 'к', 'x': 'х', 'b': 'ь', 'm': 'м',
        'n': 'н', 't': 'т', 'h': 'н', 'r': 'г',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^а-яё]', '', text)
    return original, text


def has_forbidden_words(text):
    original, cleaned = clean_text(text)
    found_words = []
    for word in FORBIDDEN_WORDS:
        if word in cleaned:
            found_words.append(word)
    
    if found_words:
        print(f"   🔍 Оригинал: '{original}'")
        print(f"   🔍 Очищено: '{cleaned}'")
        print(f"   🔍 Найдены слова: {found_words}")
        return True
    
    return False


def send_ban_log(chat_id, user_id, username, first_name, text):
    if username:
        user_link = f"@{username}"
    else:
        user_link = f"tg://user?id={user_id}"
    safe_name = first_name or "Без имени"
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    log_message = (
        f"🚫 <b>Забанен спамер</b>\n"
        f"🕐 <b>Время:</b> {now}\n"
        f"├ ID: <code>{user_id}</code>\n"
        f"├ Имя: {safe_name}\n"
        f"├ Ссылка: {user_link}\n"
        f"├ Чат: <code>{chat_id}</code>\n"
        f"└ Текст: {text}"
    )
    try:
        bot.send_message(ADMIN_ID, log_message, parse_mode="HTML")
        print("   📝 Лог отправлен админу")
    except Exception as e:
        print(f"   ❌ Ошибка отправки лога: {e}")


# ============================================================
# ОБРАБОТЧИКИ
# ============================================================
@bot.message_handler(commands=['start'], chat_types=['private'])
def start_command(message):
    user_id = message.from_user.id
    print(f"👤 /start от {user_id}")
    if user_id in authorized_users:
        bot.send_message(user_id, 
            "✅ Авторизован.\n"
            "/add_admin <пароль> <id>\n"
            "/remove_admin <id>\n"
            "/list_admins\n"
            "/add_word <слово>\n"
            "/remove_word <слово>\n"
            "/list_words\n"
            "/check_text <текст>\n"
            "/status")
    else:
        bot.send_message(user_id, "🔐 Введите пароль:")


@bot.message_handler(content_types=['text'], chat_types=['private'])
def private_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()
    print(f"📨 ЛС от {user_id}: {text[:50]}")
    if user_id in authorized_users:
        handle_admin_commands(message)
    else:
        if text == ADMIN_PASSWORD:
            authorized_users[user_id] = True
            bot.send_message(user_id, "✅ Пароль верный!")
            print(f"   ✅ Авторизован!")
        else:
            bot.send_message(user_id, "❌ Неверный пароль.")
            print(f"   ❌ Неверный пароль")


@bot.message_handler(content_types=['text'], chat_types=['group', 'supergroup'])
def group_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text or message.caption or ""
    
    print("─" * 40)
    print(f"📩 СООБЩЕНИЕ ИЗ ЧАТА")
    print(f"   Чат ID: {chat_id}")
    print(f"   Юзер ID: {user_id}")
    print(f"   Юзер: @{message.from_user.username or 'нет username'}")
    print(f"   Имя: {message.from_user.first_name}")
    print(f"   Текст: {text[:100]}")
    
    # ПРОВЕРКА 1: Запрещённые слова
    if not has_forbidden_words(text):
        print("   ✅ Проверка слов: ЧИСТО")
        return
    
    print("   ⚠️ Проверка слов: НАЙДЕНО!")
    
    try:
        # ПРОВЕРКА 2: Статус бота в чате
        bot_info = bot.get_me()
        bot_member = bot.get_chat_member(chat_id, bot_info.id)
        print(f"   🤖 Статус бота в чате: {bot_member.status}")
        
        if bot_member.status != 'administrator':
            print("   ❌ БОТ НЕ АДМИН!")
            bot.send_message(ADMIN_ID, f"⚠️ Бот не админ в чате {chat_id}!")
            return
        
        # ПРОВЕРКА 3: Дата вступления пользователя
        member = bot.get_chat_member(chat_id, user_id)
        joined_date = getattr(member, 'joined_date', None)
        
        print(f"   📅 Дата вступления юзера: {joined_date}")
        print(f"   📅 Пороговая дата: {BOT_ADDED_TIMESTAMP}")
        
        if joined_date:
            joined_str = datetime.fromtimestamp(joined_date).strftime('%d.%m.%Y %H:%M:%S')
            print(f"   📅 Вступил: {joined_str}")
            print(f"   📅 Разница: {joined_date - BOT_ADDED_TIMESTAMP} сек")
        
        # ПРОВЕРКА 4: Сравнение дат
        if not joined_date:
            print("   ⏭ РЕШЕНИЕ: ПРОПУСТИТЬ (joined_date = None)")
            return
        
        if joined_date <= BOT_ADDED_TIMESTAMP:
            print(f"   ⏭ РЕШЕНИЕ: ПРОПУСТИТЬ (joined_date {joined_date} <= порог {BOT_ADDED_TIMESTAMP})")
            return
        
        # ВСЁ ПРОВЕРЕНО — БАНИМ!
        print("   ✅ РЕШЕНИЕ: БАНИТЬ!")
        
        print("   🗑 Удаляю сообщение...")
        try:
            bot.delete_message(chat_id, message.message_id)
            print("   ✅ Сообщение удалено")
        except Exception as e:
            print(f"   ❌ Ошибка удаления: {e}")
        
        print("   🚫 Баню пользователя...")
        try:
            bot.ban_chat_member(chat_id, user_id)
            print("   ✅ Пользователь забанен!")
        except Exception as e:
            print(f"   ❌ Ошибка бана: {e}")
        
        # Лог админу
        send_ban_log(chat_id, user_id, message.from_user.username, message.from_user.first_name, text)
        
    except Exception as e:
        print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        try:
            bot.send_message(ADMIN_ID, f"⚠️ Ошибка в чате {chat_id}: {e}")
        except:
            pass


def handle_admin_commands(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text.startswith('/add_admin'):
        parts = text.split()
        if len(parts) == 3 and parts[1] == ADMIN_PASSWORD:
            try:
                new_id = int(parts[2])
                authorized_users[new_id] = True
                bot.send_message(user_id, f"✅ {new_id} добавлен.")
            except ValueError:
                bot.send_message(user_id, "❌ Неверный ID.")
        else:
            bot.send_message(user_id, "❌ /add_admin <пароль> <id>")
    
    elif text.startswith('/remove_admin'):
        parts = text.split()
        if len(parts) == 2:
            try:
                rid = int(parts[1])
                if rid == ADMIN_ID:
                    bot.send_message(user_id, "❌ Нельзя удалить главного.")
                elif rid in authorized_users:
                    del authorized_users[rid]
                    bot.send_message(user_id, f"✅ {rid} удалён.")
                else:
                    bot.send_message(user_id, "❌ Не найден.")
            except ValueError:
                bot.send_message(user_id, "❌ Неверный ID.")
        else:
            bot.send_message(user_id, "❌ /remove_admin <id>")
    
    elif text == '/list_admins':
        bot.send_message(user_id, "📋 " + "\n".join([str(u) for u in authorized_users]))
    
    elif text.startswith('/add_word'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            _, cleaned = clean_text(parts[1])
            if cleaned and cleaned not in FORBIDDEN_WORDS:
                FORBIDDEN_WORDS.append(cleaned)
                bot.send_message(user_id, f"✅ '{cleaned}' добавлено.")
            else:
                bot.send_message(user_id, "❌ Уже есть или пусто.")
        else:
            bot.send_message(user_id, "❌ /add_word <слово>")
    
    elif text.startswith('/remove_word'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            _, cleaned = clean_text(parts[1])
            if cleaned in FORBIDDEN_WORDS:
                FORBIDDEN_WORDS.remove(cleaned)
                bot.send_message(user_id, f"✅ '{cleaned}' удалено.")
            else:
                bot.send_message(user_id, "❌ Не найдено.")
        else:
            bot.send_message(user_id, "❌ /remove_word <слово>")
    
    elif text == '/list_words':
        bot.send_message(user_id, "📋 " + "\n".join(FORBIDDEN_WORDS))
    
    elif text.startswith('/check_text'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            original, cleaned = clean_text(parts[1])
            found = [w for w in FORBIDDEN_WORDS if w in cleaned]
            if found:
                bot.send_message(user_id, f"🔍 Оригинал: '{original}'\nОчищено: '{cleaned}'\nНайдены: {', '.join(found)}")
            else:
                bot.send_message(user_id, f"🔍 Оригинал: '{original}'\nОчищено: '{cleaned}'\n✅ Чисто.")
        else:
            bot.send_message(user_id, "❌ /check_text <текст>")
    
    elif text == '/status':
        bot.send_message(user_id, 
            f"✅ Бот работает!\n"
            f"Порог: {BOT_START_DATE.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Timestamp порога: {BOT_ADDED_TIMESTAMP}\n"
            f"Сейчас: {int(time.time())}\n"
            f"Слов: {len(FORBIDDEN_WORDS)}")
    
    else:
        bot.send_message(user_id, "Неизвестная команда. /start")


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    print("✅ Бот запущен!")
    print(f"📅 Порог: {BOT_START_DATE.strftime('%d.%m.%Y %H:%M:%S')} (timestamp: {BOT_ADDED_TIMESTAMP})")
    print(f"🕐 Текущее время: {int(time.time())}")
    print(f"📊 Слов: {len(FORBIDDEN_WORDS)}")
    print("=" * 50)
    
    # Отправляем тестовое сообщение админу
    try:
        bot.send_message(ADMIN_ID, f"✅ Бот запущен!\nПорог даты: {BOT_START_DATE.strftime('%d.%m.%Y %H:%M:%S')}\nТекущее время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    except:
        pass
    
    while True:
        try:
            print("🔄 Polling...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            err = str(e)
            if "409" in err or "Conflict" in err:
                print(f"⚠️ 409. Жду 10 сек...")
                time.sleep(10)
            elif "401" in err or "Unauthorized" in err:
                print(f"❌ Токен неверный!")
                break
            else:
                print(f"❌ Ошибка: {e}")
                time.sleep(5)

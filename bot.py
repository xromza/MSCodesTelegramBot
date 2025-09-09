import telebot
import time
import random_generator
from telebot import types
from telebot.types import BotCommand
from datetime import datetime, timezone, timedelta
import sqlite3
import logging
from functools import wraps
import shutil
from rich.logging import RichHandler
import threading
import json
from math import ceil
from mail import get_code
import re
from telebot.util import quick_markup
from logging.handlers import RotatingFileHandler
import os


words=["""
██╗░░██╗██████╗░░█████╗░███╗░░░███╗███████╗░█████╗░██╗░██████╗
╚██╗██╔╝██╔══██╗██╔══██╗████╗░████║╚════██║██╔══██╗╚█║██╔════╝
░╚███╔╝░██████╔╝██║░░██║██╔████╔██║░░███╔═╝███████║░╚╝╚█████╗░
░██╔██╗░██╔══██╗██║░░██║██║╚██╔╝██║██╔══╝░░██╔══██║░░░░╚═══██╗
██╔╝╚██╗██║░░██║╚█████╔╝██║░╚═╝░██║███████╗██║░░██║░░░██████╔╝
╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝╚══════╝╚═╝░░╚═╝░░░╚═════╝░""","""
░██████╗░█████╗░███████╗████████╗░██╗░░░░░░░██╗░█████╗░██████╗░███████╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝░██║░░██╗░░██║██╔══██╗██╔══██╗██╔════╝
╚█████╗░██║░░██║█████╗░░░░░██║░░░░╚██╗████╗██╔╝███████║██████╔╝█████╗░░
░╚═══██╗██║░░██║██╔══╝░░░░░██║░░░░░████╔═████║░██╔══██║██╔══██╗██╔══╝░░
██████╔╝╚█████╔╝██║░░░░░░░░██║░░░░░╚██╔╝░╚██╔╝░██║░░██║██║░░██║███████╗
╚═════╝░░╚════╝░╚═╝░░░░░░░░╚═╝░░░░░░╚═╝░░░╚═╝░░╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝""","""
░░░██╗░██╗░██╗░░██╗██╗░░██╗██╗░░██╗
██████████╗╚██╗██╔╝╚██╗██╔╝╚██╗██╔╝
╚═██╔═██╔═╝░╚███╔╝░░╚███╔╝░░╚███╔╝░
██████████╗░██╔██╗░░██╔██╗░░██╔██╗░
╚██╔═██╔══╝██╔╝╚██╗██╔╝╚██╗██╔╝╚██╗
░╚═╝░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝\n""", "thx4using\n\n"]
for i in range(4):
    for j in range(len(words[i])):
        print(words[i][j], end="")
        time.sleep(0.001)
time_of_start = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') # Дата текущей сессии
path_to_log = f"Logs/log_{time_of_start}.txt" # Путь к файлу лога
os.makedirs(os.path.abspath("Logs"), exist_ok=True)

commands = [
    BotCommand("start", "Запустить бота"),
    BotCommand("menu", "Открыть меню"),
    BotCommand("reset_states", "Сбросить состояния")
]

logger = logging.getLogger("MSCodes")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# --- Handler 1: Консоль с Rich ---
console_handler = RichHandler()
console_handler.setFormatter(logging.Formatter("%(name)s - %(message)s"))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# --- Handler 2: Запись в файл по указанному пути ---
file_handler = RotatingFileHandler(path_to_log, maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
COOLDOWN = 3
CONFIG_PATH = "Config/config.json"
ATTEMP_COOLDOWN = 3600 # в секундах
UTC_PLUS_3 = timezone(timedelta(hours=3))
config = {}
# Проверяем, существует ли директория
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

# Дефолтный конфиг
default_config = {
    "email": {
        "imap": None,
        "login": None,
        "pass": None,
    },
    "timezone": 3,
    "token": None,
    "attemp_cooldown": 3600,
    "message_cooldown": 3,
    "db_inspect_len": 5,
}

def initial_setup():
    print("Привет! Это первичная настройка бота для получения кодов от Майкрософт с почты\n\n")
    default_config["token"] = input("Введи токен бота Telegram >>> ")
    default_config["email"]["login"] = input("Введи почту аккаунта, с которого будем получать коды >>> ")
    default_config["email"]["pass"] = input("Введи пароль приложения для почтового аккаунта >>> ")
    default_config["email"]["imap"] = input("Введи адрес IMAP-сервера для этого адреса почты. Его можно найти в интернете >>> ")
    default_config["admin_pass"]= input("Введи пароль администратора для Telegram-бота >>> ")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
# Загружаем конфиг
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    initial_setup()
    config = default_config
except json.JSONDecodeError:
    print("Ошибка: Некорректный JSON в конфиге. Начинаю настройку.")
    initial_setup()
    config = default_config
logger.info("Файл конфига подключён")

COOLDOWN = config["message_cooldown"]
ATTEMP_COOLDOWN = config["attemp_cooldown"] # в секундах
UTC_PLUS_3 = timezone(timedelta(hours=config["timezone"]))
TOKEN = config["token"]
user_states = {}
logger.info("Константы из конфига загружены")

def init_db_codes():
    conn = sqlite3.connect("codes.db")
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY UNIQUE,
        num_of_act INTEGER DEFAULT 0,
        last_activated DATETIME DEFAULT NULL,
        who_activated INTEGER DEFAULT NULL
    )
''')
    conn.commit()
    conn.close()
init_db_codes()

logger.info("База данных codes подключена")

def init_db_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
            CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY UNIQUE,
              is_admin INTEGER DEFAULT 0,
              last_msg DATETIME DEFAULT CURRENT_TIMESTAMP
              )              
''')
init_db_users()

logger.info("База данных users подключена")
 # Токен Телеграм-Бота
if not TOKEN:
    raise ValueError("Токен не найден в конфиге")
bot = telebot.TeleBot(TOKEN) # Подключение к боту
bot.set_my_description("Привет! Этот бот поможет получить код для входа в аккаунт Microsoft! Отправь /start, а затем отправь уникальный код, который был выдан тебе\n\nРазработчик: xromza\nGitHub: https://github.com/xromza")
bot.set_my_commands(commands)
logger.info("Бот подключен")

def add_attemps():
    with sqlite3.connect('codes.db') as conn:
        c = conn.cursor()
        c.execute('''
                    UPDATE codes
                    SET num_of_act = 1
                    WHERE num_of_act = 0 AND ((JULIANDAY('now') - JULIANDAY(last_activated)) * 86400 > ?)
                  ''', (ATTEMP_COOLDOWN,))
        logger.info(f"Обновлено {c.rowcount} строк. Следующее обновление через {ATTEMP_COOLDOWN} секунд")

def update_attemps():
    while 1:
        logger.info("Начинаю обновление попыток")
        add_attemps()
        time.sleep(ATTEMP_COOLDOWN)

update_thread = threading.Thread(target=update_attemps, name="UpdateThread")
update_thread.daemon = True
update_thread.start()
logger.info("Запущен цикл обновления кодов")

def admin_user(user_id: int):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''
                    SELECT is_admin
                    FROM users
                    WHERE user_id = ?
                  ''', (user_id,))
        return c.fetchone()[0]

def save_config():
    json.dump(config, open("Config/config.json", "w"), ensure_ascii=False, indent=2)
    logger.info("Config был сохранён")

def anti_spam(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        logger.info(f"Пользователь {message.from_user.id}:@{message.from_user.username} написал \"{message.text}\"")
        current_time = time.time()

        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()

            # Получаем время последнего сообщения
            c.execute('SELECT last_msg FROM users WHERE user_id = ?', (message.from_user.id,))
            result = c.fetchone()

            if result is None:
                # Пользователь не существует — создаём
                c.execute('INSERT INTO users (user_id) VALUES (?)', (message.from_user.id,))
                conn.commit()
                last_msg_time = 0  # Можно считать, что это "никогда"
            else:
                last_msg_time = result[0]

            # Преобразуем дату из SQLite в timestamp
            dt = datetime.fromisoformat(str(last_msg_time))
            last_timestamp = dt.timestamp()

            # Проверяем анти-спам
            if current_time - last_timestamp < COOLDOWN:
                bot.send_message(message.from_user.id, "Слишком много сообщений, подождите немного")
                return
            now_utc_plus_3 = datetime.now(tz=UTC_PLUS_3)
            # Обновляем время последнего сообщения
            c.execute('''
                                UPDATE users
                                SET last_msg = ?
                                WHERE user_id = ?
                            ''', (now_utc_plus_3.isoformat(), message.from_user.id))
            conn.commit()

        return func(message, *args, **kwargs)

    return wrapped

def is_valid_email(email):
    # Регулярное выражение для проверки email
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

@bot.message_handler(commands=["menu"], content_types=['text'])
@anti_spam
def menu_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(types.KeyboardButton("🔑 Получить код для входа"))
    if admin_user(message.from_user.id):
        keyboard.add(types.KeyboardButton("🔄️ Изменить конфиг"))
        keyboard.add(types.KeyboardButton("👁️ Просмотреть базу данных"))
        keyboard.add(types.KeyboardButton("📁 Выгрузить логи"))
    keyboard.add(types.KeyboardButton("🛟 Инструкции"))
    #bot.send_message(message.from_user.id, "Функционал пока что не реализован", reply_to_message_id=message.id)

@bot.message_handler(func=lambda message: message.text == "🔑 Получить код для входа")
@anti_spam
def code_key(message):
    bot.send_message(message.from_user.id, text="Отправьте _уникальный код_ прямо в чат, и бот ответит вам кодом с почты!", parse_mode='MarkdownV2')

@bot.message_handler(func=lambda message: message.text == "🔄️ Изменить конфиг")
@anti_spam
def config_key(message):
    config_handler(message)

@bot.message_handler(func=lambda message: message.text == "👁️ Просмотреть базу данных")
@anti_spam
def db_key(message):
    db_inspect_handler(message)

@bot.message_handler(func=lambda message: message.text == "📁 Выгрузить логи")
@anti_spam
def logs_key(message):
    logs_handler(message)

@bot.message_handler(func=lambda message: message.text == "📁 Выгрузить логи")
@anti_spam
def instructions_key(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Для ПК", callback_data='instructions@pc'))
    keyboard.add(types.InlineKeyboardButton("Для консоли", callback_data='instructions@console'))
    bot.send_message(message.from_user.id, "Выберите вашу платформу:", reply_markup=keyboard)
@bot.message_handler(commands=["logs"], content_types=["text"])
@anti_spam
def logs_handler(message):
    if not admin_user(message.from_user.id):
        bot.send_message(message.from_user.id, "Код не найден")
        return
    name_of_log = f"Logs-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    shutil.make_archive(name_of_log, "zip", "Logs")
    with open(name_of_log+".zip", "rb") as f:
        bot.send_document(message.from_user.id, f)
    logger.warning(f"{message.from_user.id} получил папку логов.")
    os.remove(name_of_log+".zip")

def substract_attemp(code, user_id):
    with sqlite3.connect('codes.db') as conn:
        c = conn.cursor()
        c.execute('''
                UPDATE codes
                SET num_of_act = num_of_act - 1,
                last_activated = ?,
                who_activated = ?
                WHERE code = ? AND num_of_act > 0
                  ''', (datetime.now(tz=UTC_PLUS_3), user_id, code))

def make_user_admin(user_id):
    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute('''
                UPDATE users
                SET is_admin = 1
                WHERE user_id = ?
                  ''', (user_id,))
    if c.rowcount == 0:
        logger.warning(f"Пользователь {user_id} отсутствует в базе данных")
    else: 
        logger.critical(f"Пользователь {user_id} стал админом")


@bot.message_handler(commands=['start'])
@anti_spam
def start_handler(message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Получить код", callback_data="getcode"))
    keyboard.add(types.InlineKeyboardButton("Инструкции", callback_data='instructions'))
    bot.send_message(message.from_user.id, "Привет! Чтобы получить код, отправьте уникальный код, полученный у продавца, в этот чат", reply_markup=keyboard)
    with sqlite3.connect("users.db") as conn_users:
        cursor = conn_users.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.from_user.id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (message.from_user.id,))
            conn_users.commit()

@bot.message_handler(commands=["reset_states"])
@anti_spam
def reset_handler(message):
    logger.info(f"Пользователь {message.from_user.id}:@{message.from_user.username} сбросил состояния")
    bot.send_message(message.chat.id, "Состояния сброшены")
    user_states.pop(message.from_user.id, None)

def generate_codes(num: int) -> str:
    os.makedirs(os.path.abspath("Generator"), exist_ok=True)
    code = 0
    length_of_code = 16
    path_to_file = f"Generator/keys_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(path_to_file, "w") as f:
        f.write(f"Коды на 1 использование\nКоличество: {num}\n\n")
    with open(path_to_file, "a") as f:
        while code < num:
            let_code = random_generator.generate_code(length_of_code)
            with sqlite3.connect('codes.db') as conn:
                c = conn.cursor()
                c.execute('''
                            SELECT 1
                            FROM codes
                            WHERE code = ?
                          ''', (let_code, ))
                if c.fetchone() is not None:
                    continue
                else:
                    c.execute('''
                                INSERT INTO codes (code, num_of_act, last_activated)
                                VALUES (?, 1, NULL)
                              ''', (let_code,))
                    conn.commit()
                    logger.warning(f"Код {let_code} добавлен в codes")
                    f.write(let_code+"\n")
                code += 1
    logger.warning(f"Путь к файлу с кодами: {path_to_file}")
    return path_to_file


@bot.message_handler(commands=['config'])
@anti_spam
def config_handler(message):
    is_admin = admin_user(message.from_user.id)
    if not is_admin:
        bot.send_message(message.from_user.id, "Код не найден")
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Email адрес", callback_data="config@login"))
    keyboard.add(types.InlineKeyboardButton("Пароль", callback_data="config@pass"))
    keyboard.add(types.InlineKeyboardButton("IMAP-адрес", callback_data="config@imap"))
    keyboard.add(types.InlineKeyboardButton("Часовой пояс", callback_data="config@timezone"))
    keyboard.add(types.InlineKeyboardButton("Кулдаун обновления попыток получения кода", callback_data="config@attemp_cooldown"))
    keyboard.add(types.InlineKeyboardButton("Кулдаун анти-спам", callback_data="config@message_cooldown"))
    keyboard.add(types.InlineKeyboardButton("Длина вывода команды db_inspect", callback_data="config@db_inspect_len"))
    
    bot.send_message(message.from_user.id, text="Изменение конфига:", reply_markup=keyboard)


@bot.message_handler(commands=["generate"], content_types=["text"])
def handle_generator(message):
    is_admin = admin_user(message.from_user.id)
    message_id = message.from_user.id
    if not is_admin:
        bot.send_message(message_id, "Код не найден")
        return
    splitted_message = message.text.split(" ")
    if len(splitted_message) != 2:
        bot.send_message(message_id, "Команда введена неверно\n\nПравильный синтаксис:\n/generate_codes количество_кодов")
        return
    with open(generate_codes(int(splitted_message[1])), "rb") as f:
        bot.send_document(message_id, f) 

@bot.message_handler(commands=['admin'])
@anti_spam
def handle_admin(message):
    splitted_msg = message.text.split(" ")
    if admin_user(message.from_user.id):
        bot.send_message(message.chat.id, "Вы уже администратор", reply_to_message_id=message.id)
    elif len(splitted_msg) == 2 and splitted_msg[1] == config['admin_pass']:
        make_user_admin(message.from_user.id)
        bot.send_message(message.chat.id, "Вы стали администратором", reply_to_message_id=message.id)
    else:
        bot.send_message(message.chat.id, "Код не найден")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) is not None)
@anti_spam
def process_reply(message):
    if (user_states.get(message.from_user.id) == 'login'):
        if is_valid_email(message.text):
            user_states.pop(message.from_user.id)
            config["email"]["login"] = message.text
            save_config()
            logger.critical("Email в конфиге был изменён")
            bot.send_message(message.from_user.id, "Email был изменён.")
        else:
            bot.send_message(message.from_user.id, "Email введён неверно. Введите повторно")
    elif (user_states.get(message.from_user.id) in ['imap', 'pass']):
        config["email"][user_states.get(message.from_user.id)]
        save_config()
        logger.critical(f"{user_states.get(message.from_user.id)} был изменён в конфиге")
        user_states.pop(message.from_user.id)
        bot.send_message(message.from_user.id, "Изменение применено")
    elif (user_states.get(message.from_user.id) in ['timezone', 'attemp_cooldown', 'message_cooldown', 'db_inspect_len']):
        config[user_states.get(message.from_user.id)] = int(message.text)
        save_config()
        logger.critical(f"{user_states.get(message.from_user.id)} был изменён в конфиге")
        user_states.pop(message.from_user.id)
        bot.send_message(message.from_user.id, "Изменение применено")
    elif (user_states.get(message.from_user.id)[0].split('@')[0] == 'waiting_find_argument'):
        splitted = user_states.get(message.from_user.id)[0].split('@')
        bot.delete_messages(message.chat.id, [message.message_id, user_states.get(message.from_user.id)[1]])
        with sqlite3.connect(splitted[1]+'.db') as conn:
                c = conn.cursor()

                c.execute(f"PRAGMA table_info({splitted[1]})")
                columns = [col[1] for col in c.fetchall()]  # col[1] — это имя столбца

                markup = types.InlineKeyboardMarkup(row_width=len(columns))
                row = [types.InlineKeyboardButton(text=x, callback_data=f'send@{x}') for x in columns]
                markup.add(*row)
                c.execute(f'''
                            SELECT *
                            FROM {splitted[1]}
                            WHERE {splitted[2]} = ?
                        ''', (message.text,))
                result = c.fetchall()
                for _ in result:
                    row = [types.InlineKeyboardButton(text=str(x), callback_data=f'send@{x}') for x in _]
                    markup.add(*row)
                row = []
                markup.add(*row)
                bot.send_message(message.chat.id, text=f"База данных {splitted[1]}.db\n\nПоиск данных по запросу:\nСтолбец: {splitted[2]}\nЗапрос: {message.text}",reply_markup=markup)
        user_states.pop(message.from_user.id)

@bot.message_handler(commands=['db_inspect'])
def db_inspect_handler(message):
    is_admin = admin_user(message.from_user.id)
    if not is_admin:
        bot.send_message(message.from_user.id, "Код не найден")
        return
    markup = quick_markup({
        'users.db': {'callback_data': "db@users@1"},
        'codes.db': {'callback_data': "db@codes@1"},
    }, row_width=2)
    bot.send_message(message.from_user.id, "Какую базу данных вы хотите просмотреть?", reply_markup=markup)



@bot.message_handler(content_types=['text'])
@anti_spam
def code_handler(message):
    with sqlite3.connect('codes.db') as conn:
        c = conn.cursor()
        c.execute('''
                SELECT num_of_act, last_activated
                FROM codes
                WHERE code = ?                   
''', (message.text,))
        result = c.fetchone()
        if result is None:
            bot.send_message(text="Код не найден", chat_id=message.chat.id)
        else:
            if result[0] > 0:
                reply = bot.send_message(message.from_user.id, "Ищем письмо...")
                current_code = get_code(config['email']['login'], config['email']['pass'], config['email']['imap'])
                if current_code is None:
                    bot.edit_message_text("Код не пришёл или уже был использован. Ваша попытка не была потрачена, подождите 1 минуту и отправьте уникальный код повторно.", chat_id = message.chat.id, message_id=reply.id)
                    logger.info(f"Пользователь {message.from_user.id}:@{message.from_user.username} не получил код. Скрипт не нашёл его на почте")
                    return
                bot.edit_message_text(f'Код безопасности: {current_code}', message_id=reply.id, chat_id=reply.chat.id)
                substract_attemp(message.text, message.from_user.id)
                logger.info(f"Код {message.text} был активирован.")
            else:
                bot.send_message(message.from_user.id, text=f"Код уже был использован, следующая попытка будет доступна в {(datetime.fromisoformat(result[1]) + timedelta(seconds=ATTEMP_COOLDOWN)).strftime('%H:%M:%S %d.%m.%Y')} по МСК")




@bot.callback_query_handler(func= lambda call: True)
def callback_query(call):
    logger.info(f"Пользователь {call.from_user.id} нажал кнопку {call.data}")
    splitted = call.data.split("@")
    if call.data == 'instructions':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Для ПК", callback_data='instructions@pc'))
        keyboard.add(types.InlineKeyboardButton("Для консоли", callback_data='instructions@console'))
        bot.edit_message_text("Выберите вашу платформу:", reply_markup=keyboard, message_id=call.message.id, chat_id=call.from_user.id)
    elif splitted[0] == 'getcode': code_key(call.message)
    elif splitted[0] == 'instructions':
        if splitted[1] == 'pc':
            bot.edit_message_text("Инструкции для запуска на ПК: ссылка", message_id=call.message.id, chat_id=call.from_user.id)
        elif splitted[1] == 'console':
            bot.edit_message_text("Инструкции для запуска игр на консоли: ссылка",message_id=call.message.id, chat_id=call.from_user.id)
    elif splitted[0] == 'config':
        if splitted[1] in ['login', 'pass', 'imap']:
            user_states[call.from_user.id] = splitted[1] 
            bot.edit_message_text(f"Текущее значение: {config["email"][splitted[1]]}\n\nВведите новое значение", message_id=call.message.id, chat_id=call.from_user.id)
        elif splitted[1] in ['timezone', 'attemp_cooldown', 'message_cooldown', 'db_inspect_len']:
            user_states[call.from_user.id] = splitted[1]
            bot.edit_message_text(f"Текущее значение: {config[splitted[1]]}\n\nВведите новое значение", message_id=call.message.id, chat_id=call.from_user.id)
    elif splitted[0] == 'db':
        if splitted[2] != 'find':
            with sqlite3.connect(splitted[1]+'.db') as conn:
                c = conn.cursor()

                c.execute(f"SELECT COUNT(*) FROM {splitted[1]}")
                length = c.fetchone()[0]

                c.execute(f"PRAGMA table_info({splitted[1]})")
                columns = [col[1] for col in c.fetchall()]  # col[1] — это имя столбца

                markup = types.InlineKeyboardMarkup(row_width=len(columns))
                row = [types.InlineKeyboardButton(text=x, callback_data=f'send@{x}') for x in columns]
                markup.add(*row)
                c.execute(f'''
                            SELECT *
                            FROM {splitted[1]}
                            LIMIT {config['db_inspect_len']} OFFSET (? - 1)*{config['db_inspect_len']}
                        ''', (splitted[2],))
                result = c.fetchall()
                for _ in result:
                    row = [types.InlineKeyboardButton(text=str(x), callback_data=f'send@{x}') for x in _]
                    markup.add(*row)
                row = []
                if int(splitted[2]) - 1 != 0: row.append(types.InlineKeyboardButton(text="<", callback_data=f"db@{splitted[1]}@{int(splitted[2])-1}"))
                row.append(types.InlineKeyboardButton(text=splitted[2], callback_data=f'Номер страницы'))
                if int(splitted[2]) != ceil(length/config['db_inspect_len']): row.append(types.InlineKeyboardButton(text=">", callback_data=f"db@{splitted[1]}@{int(splitted[2])+1}"))
                markup.add(*row)
                markup.add(types.InlineKeyboardButton(text="Поиск", callback_data=f"db@{splitted[1]}@find"))
                bot.edit_message_text(text=f"База данных {splitted[1]}.db", reply_markup=markup, chat_id=call.from_user.id, message_id=call.message.id)
        else:
            if len(splitted) != 4:
                with sqlite3.connect(splitted[1]+'.db') as conn:
                    c = conn.cursor()

                    c.execute(f"SELECT COUNT(*) FROM {splitted[1]}")
                    length = c.fetchone()[0]

                    c.execute(f"PRAGMA table_info({splitted[1]})")
                    columns = [col[1] for col in c.fetchall()]  # col[1] — это имя столбца

                    markup = types.InlineKeyboardMarkup(row_width=len(columns))
                    for x in columns:
                        markup.add(types.InlineKeyboardButton(text=x, callback_data=f'db@{splitted[1]}@find@{x}'))
                    bot.send_message(call.from_user.id, text="По какому столбцу вести поиск?", reply_markup=markup)
            else:
                user_states[call.from_user.id] = [f'waiting_find_argument@{splitted[1]}@{splitted[3]}', call.message.id]
                bot.edit_message_text(text="Введите поисковой запрос:", chat_id=call.from_user.id, message_id=call.message.id)

    elif splitted[0] == 'send':
        bot.send_message(call.from_user.id, text=splitted[1])

bot.polling()
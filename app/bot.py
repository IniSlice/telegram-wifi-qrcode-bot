import telebot
from telebot import types 
import os
from flask import Flask, request
import bot_keyboards
from db_and_qrcode_generator import WiFiDataStorage, QRcodeGenerator
import utils
import fsm

# Получение из конфиг файла или из переменной окружения, основных констант бота
config_vars = utils.get_config_data("settings/bot_config.json")
env_vars = os.environ
TOKEN = env_vars.get('TOKEN', config_vars['TOKEN'])
APP_URL = env_vars.get('APP_URL', config_vars['APP_URL'])

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
# Экземпляр класса хранилища данных wifi сети
ks_generator = WiFiDataStorage("settings/db.json")

# Проверка состояний при вводе данных от пользователя
def is_input_state(user_or_chat_id):
    states = [
        fsm.States.S_SEND_USERNAME.value,
        fsm.States.S_SEND_PASSWORD.value,
        fsm.States.S_SEND_SECURITY_TYPE.value,
        fsm.States.S_SEND_HIDDEN_NET.value]
    return fsm.get_current_state(user_or_chat_id) in states

# Запуск бота и приветствие
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    if is_input_state(chat_id):
        bot.send_message(chat_id,
        "Вы остановились на вводе данных WiFi сети. Ожидание ввода...\n<em>Для отмены ввода - /cancel</em>",
        parse_mode='HTML')
    else:
        bot.send_message(chat_id,
            "{}, {}!\n".format(utils.get_hello_time(), message.from_user.first_name)+
            "Для генерации и отправки QR кода введите - /send\n"
            "Для вызова справки и полного списка команд введите - /help")

# Перечисление основных команд и руководство пользователя
@bot.message_handler(commands=['help'])
def help_command(message): 
    chat_id = message.chat.id
    if is_input_state(chat_id):
        bot.send_message(chat_id,
        "Вы остановились на вводе данных WiFi сети. Ожидание ввода...\n<em>Для отмены ввода - /cancel</em>",
        parse_mode = 'HTML')
    else:
        bot.send_message(
            chat_id = chat_id, 
            text = "<em>{html_text}</em>".format(html_text='\n'.join(item for item in bot_keyboards.text_help)),
            reply_markup = bot_keyboards.help_keyboard,
            parse_mode = 'HTML')

# Отмена ввода данных
@bot.message_handler(commands=['cancel'])
def cancel_commad(message):
    chat_id = message.chat.id
    if is_input_state(chat_id):
        bot.send_message(chat_id, 'Ввод данных отменён!', reply_markup=bot_keyboards.del_choose_data)
        bot.send_sticker(chat_id, 'CAACAgIAAxkBAAEBWX9fZhyo7JVbwEZ6mnAce8p2hgxHigACogIAAmMr4gkMR0GR8Z-t1hsE')
        fsm.set_state(chat_id, fsm.States.S_START.value)
    else:
        bot.send_message(chat_id, 'Данные не вводятся. Отменять нечего...')

# Изменения данных wifi сети
@bot.message_handler(commands=['settings'])
def settings_command(message):
    chat_id = message.chat.id
    if is_input_state(chat_id):
        bot.send_message(chat_id,
        "Вы остановились на вводе данных WiFi сети. Ожидание ввода...\n<em>Для отмены ввода - /cancel</em>",
        parse_mode='HTML')
    else:
        fsm.set_state(chat_id, fsm.States.S_SEND_USERNAME.value)
        bot.send_message(chat_id, "Введите имя WiFi сети (SSID):", reply_markup=bot_keyboards.keyboard_send_data('send_ssid'))

# Генерация и отправка QR кода
@bot.message_handler(commands=['send'])
def send_command(message):
    chat_id = message.chat.id
    if is_input_state(chat_id):
        bot.send_message(chat_id,
        "Вы остановились на вводе данных WiFi сети. Ожидание ввода...\n<em>Для отмены ввода - /cancel</em>",
        parse_mode='HTML')
    else:
        # получение и проверка данных wifi сети из db.json
        data = ks_generator.get_private_data(bot_user_id=str(message.from_user.id))
        if data is None:
            bot.send_message(chat_id,
            text='{:^50}'.format("Недостаточно данных для генерации QR кода!"))
            fsm.set_state(chat_id, fsm.States.S_SEND_USERNAME.value)
            bot.send_message(chat_id, "Введите имя WiFi сети (SSID):", reply_markup=bot_keyboards.keyboard_send_data('send_ssid'))
        else:
            send_qrcode_image(message, data)

# Обработка и отправка QR файла
def send_qrcode_image(message, data):
    caption_file = 'QR код для подключения к WiFi сети.'
    # получить файл изображения QR кода
    qr = QRcodeGenerator(ssid=data['ssid'], password=data['password'], security_type = data['security_type'], hidden=data['hidden'])
    wifi_code = qr.get_wifi_code()
    img_file = qr.generate_qrcode_image(wifi_code)
    # отправить файл
    bot.send_photo(message.chat.id, img_file, caption_file)

# Изменение состояния inline кнопок и изменение текста сообщений при переключении
def callback_switch_case(call, message_text, detail_message_text):
    if bot_keyboards.buttons_states[call.data] == 'Скрыть подробности':
        bot_keyboards.buttons_states[call.data] = 'Раскрыть подробности'
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, reply_markup = bot_keyboards.keyboard_send_data(call.data), parse_mode='HTML')
    else:
        bot_keyboards.buttons_states[call.data] = 'Скрыть подробности'
        bot.edit_message_text(detail_message_text, call.message.chat.id, call.message.message_id, reply_markup = bot_keyboards.keyboard_send_data(call.data), parse_mode='HTML')

# Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_command(call):
    if call.data == "send_ssid":
        callback_switch_case(call, "Введите имя WiFi сети (SSID):", bot_keyboards.text_ssid)
        bot.answer_callback_query(call.id)

    # ввести пароль в ручную
    elif call.data == "send_password":
        callback_switch_case(call, "Введите пароль от WiFi сети:", bot_keyboards.text_password)
        fsm.set_state(call.message.chat.id, fsm.States.S_SEND_PASSWORD.value)
        bot.answer_callback_query(call.id)
    
    # выбрать автогенерацию пароля
    elif call.data == 'auto_password':
        fsm.set_state(call.message.chat.id, fsm.States.S_SETTINGS.value)
        bot.edit_message_text(utils.generate_password(), call.message.chat.id, call.message.message_id, reply_markup=bot_keyboards.auto_password)
        bot.answer_callback_query(call.id)
    
    # сгенерировать новый пароль
    elif call.data == 'update_password':
        
        bot.edit_message_text(utils.generate_password(), call.message.chat.id, call.message.message_id, reply_markup=bot_keyboards.auto_password)
        bot.answer_callback_query(call.id)
    
    # сохранить сгенерированый новый пароль
    elif call.data == 'save_password':
        # получаем сгенерированный пароль и присваевыем свойству password
        # валидация и очистка данных производится в классе WiFiDataStorage
        ks_generator.password = call.message.text
        # удаляем InlineKeyboardButton кнопку перед вызовом ReplyKeyboardButton
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, "Выберите тип безопасности вашей WiFi сети:", reply_markup=bot_keyboards.choose_data_1)
        fsm.set_state(call.message.chat.id, fsm.States.S_SEND_SECURITY_TYPE.value)
        bot.answer_callback_query(call.id)
        

# Задать/изменить имя WiFi сети 
@bot.message_handler(content_types=['text'], func=lambda message: fsm.get_current_state(message.chat.id) == fsm.States.S_SEND_USERNAME.value)
def get_ssid(message):
    chat_id = message.chat.id
    try:
        # получаем имя wifi сети и присваевыем свойству ssid
        # валидация и очистка данных производится в классе WiFiDataStorage
        ks_generator.ssid = message.text
    except ValueError:
        bot.reply_to(message=message, disable_web_page_preview=True, text="Ошибка!\nНедопустимые символы!")
    except Exception as error:
        bot.send_message(chat_id, text=f"Ошибка! - {error}")
    else:
        fsm.set_state(chat_id, fsm.States.S_SETTINGS.value)
        bot.send_message(chat_id, 'Выберите способ создания пароля:', reply_markup=bot_keyboards.set_password)

# Задать/изменить пароль WiFi сети
@bot.message_handler(content_types=['text'], func=lambda message: fsm.get_current_state(message.chat.id) == fsm.States.S_SEND_PASSWORD.value)
def get_password(message):
    chat_id = message.chat.id
    try:
        # получаем пароль wifi сети и присваевыем свойству password
        # валидация и очистка данных производится в классе WiFiDataStorage
        ks_generator.password = message.text
    except ValueError:
        bot.reply_to(message=message, disable_web_page_preview=True, text="Ошибка!\nНедопустимые символы!")
    except Exception as error:
        bot.send_message(chat_id, text=f"Ошибка! - {error}")
    else:
        # удаляем пароль отправленный пользователем
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        # text = "Выберите тип безопасности вашей WiFi сети:"
        bot.send_message(chat_id, bot_keyboards.text_security_type, reply_markup=bot_keyboards.choose_data_1, parse_mode='HTML')
        fsm.set_state(chat_id, fsm.States.S_SEND_SECURITY_TYPE.value)

# Задать/изменить тип безопасности WiFi сети 
@bot.message_handler(content_types=['text'], func=lambda message: fsm.get_current_state(message.chat.id) == fsm.States.S_SEND_SECURITY_TYPE.value) 
def get_password(message):
    chat_id = message.chat.id  
    try:
        # получаем тип безопасности wifi сети и присваевыем свойству security_type
        # очистка текста от лишних символов
        clear_text = message.text.strip().upper()
        # дополнительно валидация и очистка данных производится в классе WiFiDataStorage
        # проверка выриантов введенных ответов в сообщении
        ks_generator.security_type = 'WPA/WPA2' if clear_text.startswith('ПРОПУСТИТЬ') else clear_text
    except ValueError:
        bot.reply_to(message=message, disable_web_page_preview=True, text="Ошибка!\nНедопустимые символы!")
    except Exception as error:
        bot.send_message(chat_id, text=f"Ошибка! - {error}")
    else:
        # text = "Выберите видимость вашей WiFi сети:"
       bot.send_message(chat_id, bot_keyboards.text_hidden, reply_markup=bot_keyboards.choose_data_2, parse_mode='HTML')
       fsm.set_state(chat_id, fsm.States.S_SEND_HIDDEN_NET.value)

# Задать/изменить настройки видимости WiFi сети 
@bot.message_handler(content_types=['text'], func=lambda message: fsm.get_current_state(message.chat.id) == fsm.States.S_SEND_HIDDEN_NET.value) 
def get_password(message):
    chat_id = message.chat.id  
    try:
        # получаем настройки видимости wifi сети и присваевыем свойству hidden
        # очистка текста от лишних символов
        clear_text = message.text.strip().lower()
        # проверка выриантов введенных ответов в сообщении
        if clear_text not in ('видимая сеть', 'скрытая сеть', 'пропустить этот вопрос'):
            raise ValueError
        if clear_text.startswith('пропустить') or clear_text.startswith('видимая'):
            ks_generator.hidden = False
        else:
            ks_generator.hidden = True
        # все полученные от пользователя данные wifi сети записываем в db.json
        ks_generator.set_private_data(bot_user_id=str(message.from_user.id))
    except ValueError:
        bot.reply_to(message=message, disable_web_page_preview=True, text="Ошибка!\nНедопустимые символы!")
    except Exception as error:
        bot.send_message(chat_id, text=f"Ошибка! - {error}")
    else:
        # удаляем ReplyKeyboardMarkup
        bot.send_message(chat_id=chat_id, text="Готово!\nВсе данные вашей WiFi сети сохранёны.", reply_markup=bot_keyboards.del_choose_data)
        # выводим QR изображение
        data = ks_generator.get_private_data(bot_user_id=str(message.from_user.id))
        send_qrcode_image(message, data)
        # сбрасываем состояние
        fsm.set_state(chat_id, fsm.States.S_START.value)

# Создаем список со всеми content_types
BOT_CONTENT_TYPES = [
    "text", "audio", "document", 
    "photo", "sticker", "video",
    "video_note", "voice", "location", 
    "contact", "new_chat_members", "left_chat_member", 
    "new_chat_title", "new_chat_photo", "delete_chat_photo", 
    "group_chat_created", "supergroup_chat_created", "channel_chat_created", 
    "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message"
    ]

# Перехватываем неизветные команды и сообщения разных типов контента
@bot.message_handler(content_types=BOT_CONTENT_TYPES)
def any_unknown_message(message):
    if message.content_type == 'text':
        message_text = "Неизвестная команда или сообщение.\n"
    else:
        message_text = "Бот не обрабатывает данный тип контента.\n"
    bot.reply_to(
        message=message, 
        disable_web_page_preview=True, 
        text=message_text+"Для вызова справки и полного списка доступных команд введите - /help")


# Настраиваем webhooks и Запускаем web-сервер на Heroku
def set_webhooks():
    @server.route('/' + TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200
    
    @server.route("/", methods=['GET'])
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url=APP_URL + TOKEN)
        return "Bot run from Heroku!", 200
    #Запускаем web-server
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

# Настраиваем и запускаем long_polling
def set_polling():
    #Перед запуском long_polling удаляем вебхук.
    bot.remove_webhook()
    #Очищаем очередь обновлений/сообщений
    bot.skip_pending = True
    bot.infinity_polling()

def main():
    # Проверим, есть ли переменная окружения HEROKU.
    if "WEBHOOKS_HEROKU" in os.environ:
        set_webhooks()
    else:
        #Если переменной окружения WEBHOOKS_HEROKU нет, значит это запуск с localhost.
        #Тогда запускаем long_polling
        set_polling()

if __name__ == '__main__':
    main()
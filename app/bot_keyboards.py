from telebot import types
from utils import get_config_data
import os

# Получение из конфиг файла или из переменной окружения, основных констант бота
config_vars = get_config_data("settings/bot_config.json")
env_vars = os.environ
HELP_URL = env_vars.get('HELP_URL', config_vars['HELP_URL'])

# Создание inline клавиатуры и настройка кнопок
def inline_keyboards(kb, args_buttons, one_by_one=False):
    if one_by_one:
        for data, name in args_buttons.items():
            kb.add(types.InlineKeyboardButton(text=name, callback_data=data))
    else:
        kb.add(*(types.InlineKeyboardButton(text=name, callback_data=data) for data, name in args_buttons.items()))
    return kb

#help
text_help = (
    'Для генерации и отправки QR кода введите - /send',
    'В случае наличия в базе данных бота инфомации для генерации WiFi QR кода, '
    'будет произведена отправка изображения WiFi QR кода для дальнейшего считывания с мобильного устройства.',
    'В случае же отсутсвия в базе данных бота необходимой инфомации, данные будут запрошены у пользователя.',
    'Для изменения инфомации вашей WiFi сети введите - /settings',
    'Для отмены ввода данных WiFi сети и перехода к другим командам бота введите - /cancel',
)

help_keyboard = types.InlineKeyboardMarkup()  
help_keyboard.add(types.InlineKeyboardButton('Написать разработчику', url=HELP_URL)) 


# send data
text_ssid = """Введите имя WiFi сети (SSID):
<em>Имя беспроводной сети (SSID) прописано для всех беспроводных устройств в вашей сети.
- Должно быть задано цифрами, буквами и/или символами в ASCII кодировки 
(латинский алфавит, десятичные цифры, символы, и т.д.).
- Допускается использовать цифры [0-9] и символы [-, _].
- Длина имени должна быть до 32 символов.</em>
"""

text_password = """Введите пароль от WiFi сети:
<em>Пароль используется для подключения к WiFi сети, на всех беспроводных устройств в вашей сети.
- Должен быть задан цифрами, буквами и/или символами в ASCII кодировки 
(латинский алфавит, десятичные цифры, символы, и т.д.).
- Должен содержать хотябы по одной букве в верхнем [A-Z] и одной в нижнем регистре [a-z]
- Должен содержать хотябы одну цифру [0-9]
- Длина пароля должна быть от 8 до 64 символов.</em>
"""

text_security_type = """Выберите тип безопасности WiFi сети:
<em>'NOPASS' -  Отключить защиту беспроводной WiFi сети.
(Если она отключена, беспроводные устройства могут подключаться к роутеру без пароля от вашей WiFi сети.)
'WPA/WPA2' - Выбрать защиту на основе WPA с использованием общего ключа.
'WEP' - Выбрать защиту 802.11 WEP.
'Пропустить этот вопрос' - будет выбрано значение по умолчанию: 'WPA/WPA2'</em>
"""

text_hidden = """Выберите видимость WiFi сети (SSID):
<em>'Видимая сеть' - имя вашей имя WiFi сети (SSID) передается открыто и присутствует в списке доступных подключений.
'Скрытая сеть' - вы не наблюдаете имя вашей имя WiFi сети (SSID) в списке доступных подключений.
'Пропустить этот вопрос' - будет выбрано значение по умолчанию: 'Видимая сеть'</em>
"""

buttons_states = {
    'send_ssid': 'Раскрыть подробности',
    'send_password': 'Скрыть подробности',
    'send_security_type': 'Раскрыть подробности',
    'send_hidden': 'Раскрыть подробности',
    }

# Создание inline клавиатуры и настройка кнопок
def keyboard_send_data(callback_data):
    data = types.InlineKeyboardMarkup()
    data.add(types.InlineKeyboardButton(text=buttons_states[callback_data], callback_data=callback_data))
    return data

# set password
set_password = types.InlineKeyboardMarkup()
set_password = inline_keyboards(set_password, {'auto_password': 'Сгенерировать', 'send_password': 'Ввести вручную'})

auto_password = types.InlineKeyboardMarkup()
auto_password = inline_keyboards(auto_password, {'update_password': 'Обновить', 'save_password': 'Сохранить'})

# choose data
choose_data_1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
choose_data_1.row(*[types.KeyboardButton(text=b) for b in ('WPA/WPA2', 'WEP', 'NOPASS')])
choose_data_1.add(types.KeyboardButton(text='Пропустить этот вопрос'))

choose_data_2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
choose_data_2.row(*[types.KeyboardButton(text=b) for b in ('Видимая сеть', 'Скрытая сеть')])
choose_data_2.add(types.KeyboardButton(text='Пропустить этот вопрос'))

del_choose_data = types.ReplyKeyboardRemove()
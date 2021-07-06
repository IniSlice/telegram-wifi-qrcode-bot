import secrets
import random
import string
import re
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import json
from json.decoder import JSONDecodeError

tzlocal = tzlocal()

# Получение данных для бота из конфиг файла 
def get_config_data(fname):
    default_data = {"data": {"TOKEN": "", "APP_URL": "", "BOT_URL": "", "HELP_URL": ""}}
    try:
        with open(fname, 'r') as fb:
            js_data = json.load(fb)
            return js_data.get('data')
    except (IOError,  FileNotFoundError, JSONDecodeError) as errors:
        print(f"Не удалось коректно считать файл!\nОшибка: {errors}")
        with open(fname, 'w') as fb:
            json.dump(default_data, fb, indent=4)
            print('Файл перезаписался!')
            return default_data['data']
    except Exception as er:
            print("Другая ошибка!")

# Генерация пароля
def generate_password(symbols=False):
    # алфавитно-цифровой пароль, который должен содержать по крайней мере одну строчную букву,
    # одну заглавную букву и одну цифру. И быть длиной от 8 до 64 символов
    alphabet = string.ascii_letters + string.digits
    # проверка пароля по шаблону 
    pattern = re.compile(r"^(?=.*[0-9].*)(?=.*[a-z].*)(?=.*[A-Z].*)[0-9a-zA-Z"+string.punctuation+r"]{8,64}$")
    if symbols:
        alphabet += string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(random.randint(8, 20)))
        if pattern.match(password):
            return password

#Получение время суток для приветствия пользователя
def get_hello_time():
    time_messages = ('Доброй ночи', 'Доброе утро', 'Добрый день', 'Добрый вечер')
    now_time = datetime.now(tzlocal)
    start_time = datetime.strptime('00:00:00', '%H:%M:%S')
    for message in time_messages:
        range_time=start_time+timedelta(hours=5, minutes=59, seconds=59, milliseconds=999)
        if start_time.time()<=now_time.time()<=range_time.time():
            return message
        start_time = range_time+timedelta(milliseconds=1)

if __name__ == "__main__":
    get_hello_time()







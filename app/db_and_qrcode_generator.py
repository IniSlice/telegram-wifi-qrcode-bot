import qrcode
import getpass
import json
from json.decoder import JSONDecodeError
import re
from string import punctuation

class WiFiDataStorage():
    def __init__(self, storage_path):
        self.__storage_path = storage_path
        self._system_username = None
        self._ssid = None
        self._password = None
        self._security_type = "WPA/WPA2"
        self.hidden = False
    
    @property
    def system_username(self):
        self._system_username = getpass.getuser()
        return self._system_username
    
    @staticmethod
    def is_cyrillic(text):
        """ Проверка на наличие символов кириллицы """
        return bool(re.search('[\u0400-\u04FF]', text))
    

    @staticmethod
    def clean_ssid(text):
        """ Валидатор введенных данных(ssid)"""
        # очистка текста от лишних пробелов
        clear_text = re.sub(r"\s+", '', text.strip())
        pattern_password = re.compile(r"^[0-9a-zA-Z"+punctuation+r"]{,32}$")
        res = pattern_password.match(clear_text)
        if res:
            return res.string
    
    @staticmethod
    def clean_password(text):
        """ Валидатор введенных данных(password)"""
        # очистка текста от лишних пробелов 
        clear_text = re.sub(r"\s+", '', text.strip())
        # проверка пароля по шаблону 
        pattern_password = re.compile(r"^(?=.*[0-9].*)(?=.*[a-z].*)(?=.*[A-Z].*)[0-9a-zA-Z"+punctuation+r"]{8,64}$")
        res = pattern_password.match(clear_text)
        if res:
            return res.string

    @property
    def ssid(self):
        return self._ssid

    @ssid.setter
    def ssid(self, value):
        if not isinstance(value, str):
            raise TypeError(f'Ошибка! Значение {value} не является типом - str')
        if self.clean_ssid(value) is None:
            raise ValueError(f'Ошибка! Значение {value} содержит недопустимые символы!')
        self._ssid = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if not isinstance(value, str):
            raise TypeError(f'Ошибка! Значение {value} не является типом - str')
        if self.clean_password(value) is None:
            raise ValueError(f'Ошибка! Значение {value} содержит недопустимые символы!')
        self._password = value
    
    @property
    def security_type(self):
        return self._security_type
    
    @security_type.setter
    def security_type(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Ошибка! Значение '{value}' не является типом - str")
        allowable_values = ('NOPASS', 'WPA', 'WPA2', 'WPA/WPA2', 'WEP')
        if re.sub(r"\s+", '', value.strip()) not in allowable_values:
            raise ValueError(f"Ошибка! Значение '{value}' не найдено в списке допустимых значений - '{allowable_values}'")
        self._security_type = value

    def __get_data(self):
        with open(self.__storage_path, 'r') as fb:
            js_data = json.load(fb)
            users = js_data.get("users")
        return js_data, users

    def set_private_data(self, bot_user_id):
        data = {"ssid":self.ssid, "password":self.password, "security_type":self.security_type, "hidden":self.hidden}
        try:
            js_data, users = self.__get_data()
            with open(self.__storage_path, 'w') as fb:
                users.update({bot_user_id: data})
                json.dump(js_data, fb, indent=4)
        except (IOError,  FileNotFoundError, JSONDecodeError) as errors:
            print(f"Не удалось коректно записать файл базы данных!\nОшибка: {errors}")
        except Exception as er:
            print(f"Другая ошибка при записи в базу данных: {er}")
    
    def get_private_data(self, bot_user_id):
        default_data = {"users": {bot_user_id: {"ssid": "", "password": "", "security_type": "", "hidden": False}}}
        try:
            _, users = self.__get_data()
            if users is None:
                raise TypeError
            current_user_data = users.get(bot_user_id)
            if any(not item for item in list(current_user_data.values())[:-1]):
                raise ValueError
            return current_user_data
        except FileNotFoundError:
            with open(self.__storage_path, 'w') as fb:
                json.dump(default_data, fb, indent=4)
                print('Файл базы данных не был найден!\nФайл перезаписался!')
        except ValueError:
            print("В базе данных отсутствует одно или несколько значений!")
        except (IOError, JSONDecodeError, TypeError) as errors:
            print(f"Не удалось коректно считать файл базы данных!\nОшибка: {errors}")
        except Exception as er:
            print(f"Другая ошибка при считывании из базы данных: {er}")

class QRcodeGenerator(WiFiDataStorage):
    def __init__(self, ssid, password, security_type = 'NOPASS', hidden = False):
        self.ssid = ssid
        self.password = password
        self.security_type = security_type
        self.hidden = False
    
    @property
    def raw_data(self):
        """ Получение необработанных данных wifi сети """
        data = {
            'ssid': self.ssid,
            'password': self.password,
            'security_type': self.security_type,
            'hidden_network': self.hidden,
            }
        return data
    
    def get_wifi_code(self):
        """ Формирование и получение строки с данными wifi сети """
        if self.security_type in ('WPA', 'WPA2', 'WPA/WPA2', 'WEP') and self.password is None:
            raise TypeError(f"При типе безопасности WiFi - {self.security_type}\nПароль не может отсутсвовать!")
        if self.security_type == 'NOPASS':
            wifi_code = f"WIFI:T:{self.security_type};S:{self.ssid};H:{self.hidden};;"
        else:
            wifi_code = f"WIFI:T:{self.security_type};S:{self.ssid};P:{self.password};H:{self.hidden};;"
        return wifi_code

    def generate_qrcode_image(self, fdata, size=(1000, 1000), fname=None):
        """ Генерация изображение QR кода на основе полученной сформированной строки с данными wifi сети """
        if size and (not isinstance(size, tuple)):
            raise TypeError(f"Ошибка! Значение '{size}' не является типом - tuple")
        # генерируем qr-код
        image_obj = qrcode.make(fdata)
        # Задаём новый размер изображения
        image_obj = image_obj.resize(size)
        return image_obj
    
    def show_qrcode_image(self):
        """ Отрытие и просмотр изображения QR кода"""
        image_obj = self.generate_qrcode_image()
        image_obj.show()


    

    






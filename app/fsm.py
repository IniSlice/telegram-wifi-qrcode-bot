from enum import Enum

# Класс перечислений(константы состояний)
class States(Enum):
    S_START = 0 # Начало нового диалога
    S_SETTINGS = 1
    S_SEND_USERNAME = 2
    S_SEND_PASSWORD = 3
    S_SEND_SECURITY_TYPE = 4
    S_SEND_HIDDEN_NET = 5

states_dict = {}

# Получение текущего состояния 
def get_current_state(user_id):
    # Если такого ключа почему-то не оказалось то возвращаем значение по умолчанию - начало диалога
    return states_dict.get(str(user_id), States.S_START.value)

# Установка нового состояния
def set_state(user_id, value):
    try:
        states_dict.update({str(user_id):value})
    except Exception as e:
        print('Ошибка словаря состояний', e)
        return False
    else:
        return True
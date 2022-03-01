from datetime import timedelta
import time

CRIMGOBOT_TOKEN = '5019874620:AAGNtS_qhsu59PLSeMSbYWnnoy4Aac8m1ZU'

PAYMENTS_PROVIDER_TOKEN='381764678:TEST:32687'
SHUTTLE_IMAGE_URL = 'https://ecotechnica.com.ua/images/-foto4/987-Jaguar-Land-Rover_vector-ecotechnicacomua-1.jpg'

DATABASE = {
    'host': 'localhost',
    'port': '5432',
    'username': 'postgres',
    'password': 'postgres',
    'database': 'crimgo'
}

# часовой пояс
TIME_OFFSET = timedelta(hours=3)

# максимальное время ожидания, столько максимально может пройти от момента первого заказа до отправления 
MAX_WAIT_TIME = timedelta(minutes = 30)

# минимальное время ожидания, Столько минимально необходимо времени после заказа поездки, чтобы пассажир собрался и вышел
MIN_WAIT_TIME = timedelta(minutes = 10)

# Длительность посадки пассажиров
BOARDING_TIME = timedelta(minutes = 3)

# Длительность высадки пассажиров
UNBOARDING_TIME = timedelta(minutes = 2)

# Время за которое оповещаем пассажира
ALRM_TIME = timedelta(minutes = 5)

# Время в пути между 2мя соседними остановками. Для упрощения и расчётов
STP_TRVL_TIME = timedelta(minutes = 3)

# Общее время в пути без остановок
TRVL_TIME = timedelta(minutes = 10)




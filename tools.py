"""
    Модуль со всеми функциями, необходимыми для работы скрипта.
    При запуске файла, как скрипт, запустится script().
    Для корректной работы, необходимо сначала обновить config.py согласно его описанию.
    При запросe к google sheets проходит примерно 15 секунд.
    Заказы построчно вставлются в таблицу, чтобы избежать ошибок, связанных с неуникальностью поля id или order_number

"""
import os
from datetime import datetime, timedelta
from typing import Optional

import httplib2
import psycopg2
import requests
import xml.etree.ElementTree as Et
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import *


def convert_order_from_gs_list_to_tuple(order: list) -> Optional[tuple]:
    """
    Преобразует order из формата ['id', 'order_number', 'dollar_price', 'delivery_time']
                        в формат (id, order_number, dollar_price, 'delivery_time', ruble_price).
    delivery_time преобразуется из формата 'дд.мм.гггг' в формат 'гггг-мм-дд',
    добавляется новое поле ruble_price.
    В случае, если данные некорректные, ничего не возращает, сообщение об ошибке записывается в лог

    """
    try:
        id = int(order[0])
        order_number = int(order[1])
        dollar_price = float(str(order[2]).replace(',', '.'))
        delivery_time = datetime.strptime(order[3], "%d.%m.%Y").strftime('%Y-%m-%d')
        ruble_price = round(dollar_price * get_current_dollar_rate(), 2)

        order = (id, order_number, dollar_price, delivery_time, ruble_price)
        return order

    except ValueError as error:
        log("convert_order_from_gs_list_to_tuple: " + str(error))


def create_db() -> None:
    """
    Создает базу данных и таблицу orders в ней.
    Параметры создания БД берутся из config.py

    """
    cursor = get_db_cursor('postgres', USER, PASSWORD, HOST, isolation_level=True)
    cursor.execute("CREATE DATABASE %s;" % DEFAULT_DB_NAME)
    cursor.connection.commit()

    cursor = get_db_cursor(DEFAULT_DB_NAME, USER, PASSWORD, HOST)
    cursor.execute("CREATE TABLE orders("
                   "id int not null primary key,"
                   "order_number int not null,"
                   "dollar_price double precision not null,"
                   "delivery_time date not null,"
                   "ruble_price double precision not null,"
                   "CONSTRAINT order_unique UNIQUE (order_number));")
    cursor.connection.commit()


def delete_order_from_db(id: int) -> None:
    """
    Удаляет заказ из таблицы заказов локальной БД, используя его id

    - *id*: id заказа, который необходимо удалить

    """
    cursor = get_db_cursor(DEFAULT_DB_NAME, USER, PASSWORD, HOST)
    cursor.execute("DELETE FROM orders WHERE id = %s;" % (id,))
    cursor.connection.commit()


def get_current_dollar_rate() -> float:
    """
    Возвращает актуальный курс доллара.

    url формируется по шаблону, в который вставляется две даты - диапазан, за который нужно получить курс доллара.
    Данный диапазон - это последние 2 недели, так как курс не обновляется в праздничные дни.
    Например, в новогодние праздники курс может не обновлятся около 10 дней.
    С помощью get_dollar_rate_xml() получаем XML с курсом доллара за 2 последние недели.
    dollar_rate_xml[-1][1].text - это последний курс, доступный в XML

    """
    current_date = datetime.now().date()
    two_weeks_ago = current_date - timedelta(days=14)
    url = 'https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={0}&date_req2={1}&VAL_NM_RQ=R01235' \
        .format(two_weeks_ago.strftime("%d/%m/%Y"), current_date.strftime("%d/%m/%Y"))

    def get_dollar_rate_xml():
        """
        Возращает XML с курсом доллара.
        При тестировании обнаружено, что сайт ЦБ не всегда выдает XML, что вызывает ошибку типа ParseError.
        Для решения данной проблемы используется рекуривный вызов данной функции.
        Сообщение об ошибке записывается в лог

        """
        try:
            dollar_rate_xml = Et.fromstring(requests.get(url).content)
        except Et.ParseError as exception:
            message = "Произошла неудачная попытка получить XML с курсом доллара. Описание ошибки:\n" + str(exception)
            log(message)
            dollar_rate_xml = get_dollar_rate_xml()

        return dollar_rate_xml

    dollar_rate_xml = get_dollar_rate_xml()
    current_dollar_rate = float(dollar_rate_xml[-1][1].text.replace(',', '.'))
    return current_dollar_rate


def get_db_cursor(dbname, user, password, host, isolation_level=False):
    """
        Подключается к базе данных и возвращает объект библиотеки pcycopg для работы с ней.
        После окончания работы необходимо обязательно вызвать <cursor>.connection.commit() для сохранения работы;
        вместо <cursor> - имя вашего объекта подключения

        - *dbname*: str
        - *user*: имя пользователя
        - *password*: пароль
        - *host*: адрес хоста
        - *isolation_level*: по дефолту Fasle; если True, позволяет создать новую базу данных

    """
    connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    if isolation_level is True:
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    return cursor


def get_google_sheet_db() -> list[tuple]:
    """
    Возвращает список заказов, полученных из google sheets с добавления столбца ruble_price.
    В buffer записываются только строки, содержащие все столбцы.
    Обработка ошибок, связанных с некоректными данными, происходит в convert_order_from_gs_list_to_tuple()

    """
    buffer = [order for order in get_sheet_data() if len(order) == 4]
    db = []
    for order in buffer:
        convert_order = convert_order_from_gs_list_to_tuple(order)
        if convert_order is not None:
            db.append(convert_order)
    return db


def get_local_db() -> list[tuple]:
    """
    Возращает таблицу заказов из БД, находящейся на машине.
    Данные подключения к БД берутся из config.py
    Формат таблицы - [(id, order_number, dollar_price, 'delivery_time', ruble_price),...]
    
    """
    cursor = get_db_cursor(DEFAULT_DB_NAME, USER, PASSWORD, HOST)
    cursor.execute("SELECT * FROM orders ORDER BY id;")
    db = []
    for order in cursor.fetchall():
        db.append((order[0], order[1], order[2], str(order[3]), order[4]))
    cursor.connection.commit()
    return db


def get_service_sacc():
    """
    Возвращает объект, с помощью которого можно получить данные из Google Sheets

    """
    credentials_json = os.path.dirname(__file__) + CREDENTIALS  # файл доступа, полученный из Google API
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials_service = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scopes).authorize(
        httplib2.Http())
    return build('sheets', 'v4', http=credentials_service)


def get_sheet_data() -> list:
    """
    Возвращает данные из Google sheets в виде списка

    - *spreadsheetId*: id таблицы, которое можно получить из url таблицы
    - *range*: строка с диапазоном таблицы, который необходимо обработать

    spreadsheetId и range берутся из config.py

    """
    response = get_service_sacc().spreadsheets().values().get(
        spreadsheetId=SPREAD_SHEET_ID,
        range=RANGE
    ).execute()
    return response['values']


def insert_into_db(order: tuple) -> None:
    """
    Вставляет order в таблицу заказов локальной БД.

    - *order*: кортеж формата (id, order_number, dollar_price, 'delivery_time', ruble_price)

    """
    cursor = get_db_cursor(DEFAULT_DB_NAME, USER, PASSWORD, HOST)
    try:
        cursor.execute("INSERT INTO orders VALUES %s;" % str(order))
    except psycopg2.errors.UniqueViolation as error:
        log('insert_into_db: ' + str(error))
    cursor.connection.commit()


def log(message: str) -> None:
    """
    Простое логирование. Имя файла берется из config.py

    - *message*: сообщение для записи в лог

    """
    log_file = open(LOG_FILE_NAME, 'a')
    log_file.write(f"{message}-{datetime.now()}\n")
    log_file.close()


def script() -> None:
    """
        Основной скрипт. Создает БД с таблицей заказов и постоянно обновляет ее, согласно данным из Google Sheets
        Если БД уже существует, перезаписывает ее, сообщение об ошибке записывается в лог.

    """
    try:
        create_db()
    except psycopg2.errors.DuplicateDatabase as error:
        message = "База с именем {} уже существует. Она будет перезаписана. Код ошибки:\n".format(DEFAULT_DB_NAME)\
                  + str(error)
        log(message)
    while True:
        update_db()


def update_db() -> None:
    """
    Сравнивает таблицу заказов, полученную из Google Sheets с локальной.
    Если есть отличия, обновляет локальную таблицу заказов.
    После выполнения выводит сообщение о завешении.

    """
    local_db = get_local_db()
    google_sheet_db = get_google_sheet_db()
    diffs = set(local_db) ^ set(google_sheet_db)

    [delete_order_from_db(diff[0]) for diff in diffs if diff in local_db]
    [insert_into_db(diff) for diff in diffs if diff in google_sheet_db]

    print("Database update - SUCCESSFUL", datetime.now())


if __name__ == '__main__':
    script()

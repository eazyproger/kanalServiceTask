"""
    Модуль для отправки уведомлений в Телеграм.
    Отправляет уведомления с номерами заказов, у которых истек срок доставки.
    Чат отправки и токен бота берется из config.py

"""
from datetime import datetime
from time import sleep

import requests
from schedule import every, repeat, run_pending

from tools import get_db_cursor
from config import DEFAULT_DB_NAME, USER, PASSWORD, HOST, CHAT_ID, TOKEN


def send_telegram_message(message: str) -> None:
    """
    Отправляет сообщение в Телеграмм с заданным в config.py CHAT_ID

    - *message*: сообщение, которое необходимо отправить

    """
    url = "https://api.telegram.org/bot"
    url += TOKEN
    method = url + "/sendMessage"

    r = requests.post(method, data={
         "chat_id": CHAT_ID,
         "text": message
          })

    if r.status_code != 200:
        raise Exception("post_text error")


@repeat(every().day.at("12:00"))
def send_notifications():
    """
    Основная функция модуля.
    Берет данные из таблицы заказов локальной базы данных и проверяет их на истечение срока поставки.
    Если срок поставки истек, в формирующееся сообщение добавляется номер этого заказа.
    Получившееся сообщение отправляет через Телеграм.
    Срабатывает 1 раз в сутки в 12:00, согласно локальному времени

    """
    cursor = get_db_cursor(DEFAULT_DB_NAME, USER, PASSWORD, HOST)
    cursor.execute("SELECT * FROM orders;")
    db = cursor.fetchall()
    message = 'Истек срок поставки по следующим заказам:\n'
    for order in db:
        if datetime.now().date() > order[3]:
            message = '{0}\t{1}\n'.format(message, str(order[1]))

    send_telegram_message(message)


if __name__ == '__main__':
    while True:
        run_pending()
        sleep(1)

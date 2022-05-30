ОПИСАНИЕ

    Скрипт копирует таблицу заказов из Google Sheets  в локальную БД Postgres, 
    после чего постоянно обновляет ее.
    Сервис уведомлений notifications ежедневно рассылает уведомление с номерами просроченных заказов.
    Также присутствует реализация Django-сайта, который выводит таблицу заказов.
    Google Sheet: https://docs.google.com/spreadsheets/d/1WJMINoH3PLSxZOh7O7vFGeVCKrq-JadilQ00yB2JhOI/edit#gid=0
    

УСТАНОВКА И ЗАПУСК

  Запуск скрипта
  
    Для запуска скрипта необходимы установленные python, pip, git и postgres
    
    Переходим в директорию, в которой будет располагаться проект
    
    Клонируем проект с git-репозитория:
      git clone https://github.com/eazyproger/kanalServiceTask.git
      
    Переходим в директорию проекта:
      cd kanakServiceTask/
    
    Создаем виртуальное окружение:
      pip install virtualenv
      virtualenv venv
      source venv/bin/activate
      
    Устанавливаем зависимости:
      pip install -r ./requirements.txt

    Меняем пароль в config.py на пароль администратора
    или
    Меняем пароль администратора в базе данных postgres:
      sudo -u postgres psql postgres
      \password postgres

    Запускаем скрипт:
      python tools.py

  Запуск сервиса уведомлений
    
    Для начала необходимо начать чат с ботом @kanalServiceNotifications_bot отправив ему любое сообщение
    Далее необходимо перейти по данной ссылке https://api.telegram.org/bot5568286805:AAE_Z0NfwL3QSJgW_o9k9waCrQCs8hXR054/getUpdates,
    в котором найти последнюю сущность "chat", содержащую "id" чата
    Изменить CHAT_ID в config.py на полученный "id"
    Запустить скрипт:
      python notifications.py
      
    Примечание: правильней было бы, чтобы бот отправлял chat_id в ответ на сообщение пользователя,
    но для этого пришлось бы запускать дополнительный скрипт, обрабатывающий сообщения пользователей
    на каком-либо сервере или же локально, то выходит за рамки данного ТЗ, хотя и не является проблемой

  Запуск Django
    
    Через текстовый редактор меняем пароль в kanalServiceTask/kanalServiceTask/setting.py 
    строка 82 на пароль администратора
    
    Переходим в папку с Django-проектом:
      cd kanalServiceTask/
    
    Запускаем сервер:
      ./manage.py runserver
      
    Сайт с таблицей будет доступен по указанному ip

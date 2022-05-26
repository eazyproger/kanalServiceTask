ОПИСАНИЕ

    Скрипт копирует таблицу заказов из Google Sheets  в локальную БД Postgres, 
    после чего постоянно обновляет ее.
    Также присутствует реализация Django-сайта, который выводит таблицу заказов.

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

    Запускаем скрипт:
      python tools.py

  Запуск Django
    
    Через текстовый редактор меняем пароль в kanalServiceTask/kanalServiceTask/setting.py 
    строка 82 на пароль администратора
    
    Переходим в папку с Django-проектом:
      cd kanalServiceTask/
    
    Запускаем сервер:
      ./manage.py runserver
      
    Сайтс таблицей будет доступен по указанному ip

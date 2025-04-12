#!/bin/bash

# Остановка приложения, если оно запущено
pkill -f gunicorn

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание директорий
mkdir -p uploads
mkdir -p logs

# Применение миграций базы данных
flask db upgrade

# Запуск приложения через gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:app \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon 
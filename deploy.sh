#!/bin/bash

# Остановка приложения, если оно запущено
pkill -f gunicorn

# Создание и активация виртуального окружения
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Создание необходимых директорий
mkdir -p uploads
mkdir -p logs
chmod 755 uploads
chmod 755 logs

# Применение миграций базы данных
export FLASK_APP=app.py
export FLASK_ENV=production
flask db upgrade

# Запуск приложения через gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:app \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon

# Проверка статуса
sleep 2
if pgrep -f gunicorn > /dev/null; then
    echo "Приложение успешно запущено"
else
    echo "Ошибка при запуске приложения"
    exit 1
fi 
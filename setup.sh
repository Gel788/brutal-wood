#!/bin/bash

# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Установка необходимых пакетов
sudo apt-get install -y python3-pip python3-dev nginx postgresql postgresql-contrib

# Установка и настройка PostgreSQL
sudo -u postgres psql -c "CREATE USER u3083270 WITH PASSWORD 'oT85mNVVm93TMHbv';"
sudo -u postgres psql -c "CREATE DATABASE avito OWNER u3083270;"

# Настройка Nginx
sudo tee /etc/nginx/sites-available/avito << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/u3083270/avito/static;
    }

    location /uploads {
        alias /home/u3083270/avito/uploads;
    }
}
EOF

# Активация конфигурации Nginx
sudo ln -s /etc/nginx/sites-available/avito /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Настройка брандмауэра
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable

# Создание директории для приложения
mkdir -p ~/avito
cd ~/avito

# Клонирование репозитория
git clone https://github.com/Gil788/brutal-wood.git .

# Установка прав
chmod +x deploy.sh
chmod +x setup.sh

# Запуск развертывания
./deploy.sh 
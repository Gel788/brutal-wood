#!/bin/bash

# Настройки FTP
FTP_HOST="31.31.196.49"
FTP_USER="u3083270"
FTP_PASS="14mEFP0K1Df2Jds3"
FTP_DIR="/avito"

# Создание временной директории
TEMP_DIR="temp_deploy"
mkdir -p $TEMP_DIR

# Копирование необходимых файлов
cp -r app.py models.py forms.py utils.py wsgi.py requirements.txt $TEMP_DIR/
cp -r templates $TEMP_DIR/
cp -r static $TEMP_DIR/
mkdir -p $TEMP_DIR/uploads
mkdir -p $TEMP_DIR/logs

# Создание .htaccess
cat > $TEMP_DIR/.htaccess << EOF
RewriteEngine On
RewriteBase /
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.php/$1 [L]

# Защита от доступа к системным файлам
<FilesMatch "^\.">
    Order allow,deny
    Deny from all
</FilesMatch>

# Защита от доступа к конфигурационным файлам
<FilesMatch "\.(env|config\.py|\.git)">
    Order allow,deny
    Deny from all
</FilesMatch>

# Настройка кодировки
AddDefaultCharset UTF-8

# Настройка MIME-типов
AddType application/x-httpd-php .php
AddType text/html .html
AddType text/css .css
AddType text/javascript .js
AddType image/jpeg .jpg .jpeg
AddType image/png .png
AddType image/gif .gif

# Настройка кэширования
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
</IfModule>
EOF

# Создание .env
cat > $TEMP_DIR/.env << EOF
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://u3083270:oT85mNVVm93TMHbv@localhost:5432/avito
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif
EOF

# Загрузка через FTP
echo "Загрузка файлов на сервер..."
lftp -u $FTP_USER,$FTP_PASS $FTP_HOST << EOF
mirror -R $TEMP_DIR $FTP_DIR
quit
EOF

# Очистка временных файлов
rm -rf $TEMP_DIR

echo "Развертывание завершено!" 
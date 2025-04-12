import os
import json
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
from app import app, logger

def allowed_file(filename):
    """Проверяет, что файл имеет допустимое расширение"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_photos(files):
    """Сохраняет загруженные фотографии и возвращает список путей к ним"""
    if not files:
        return None
    
    saved_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            # Создаем уникальное имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(file.filename)
            unique_filename = f"{timestamp}_{filename}"
            
            # Сохраняем файл
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Проверяем и оптимизируем изображение
            try:
                with Image.open(filepath) as img:
                    # Проверяем размер
                    if img.size[0] > 1200 or img.size[1] > 1200:
                        img.thumbnail((1200, 1200))
                        img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                logger.error(f"Ошибка при обработке изображения {filepath}: {str(e)}")
            
            saved_paths.append(unique_filename)
    
    return json.dumps(saved_paths) if saved_paths else None

def delete_photos(photos_json):
    """Удаляет фотографии из файловой системы"""
    if not photos_json:
        return
    try:
        photos = json.loads(photos_json)
        for photo in photos:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo)
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        logger.error(f"Ошибка при удалении фотографий: {str(e)}")

def generate_repost_times(reposts_per_day, start_date, end_date):
    """Генерирует времена для репостов"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        total_days = (end - start).days + 1
        total_reposts = reposts_per_day * total_days
        
        # Генерируем случайные времена в течение дня
        times = []
        for _ in range(total_reposts):
            random_time = start + timedelta(
                days=random.randint(0, total_days-1),
                hours=random.randint(9, 20),
                minutes=random.randint(0, 59)
            )
            times.append(random_time.strftime('%Y-%m-%dT%H:%M'))
        
        return json.dumps(sorted(times))
    except Exception as e:
        logger.error(f"Ошибка при генерации времен репостов: {str(e)}")
        return json.dumps([]) 
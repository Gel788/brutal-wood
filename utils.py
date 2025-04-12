import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def allowed_file(filename):
    """Проверяет, что файл имеет допустимое расширение"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Проверяем и оптимизируем изображение
            try:
                with Image.open(filepath) as img:
                    # Проверяем размер
                    if img.size[0] > 1200 or img.size[1] > 1200:
                        img.thumbnail((1200, 1200))
                        img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                current_app.logger.error(f"Ошибка при обработке изображения {filepath}: {str(e)}")
            
            saved_paths.append(unique_filename)
    
    return json.dumps(saved_paths) if saved_paths else None

def delete_photos(photo_paths):
    """Удаляет фотографии по списку путей"""
    if not photo_paths:
        return
    
    try:
        paths = json.loads(photo_paths)
        for path in paths:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], path)
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        current_app.logger.error(f"Ошибка при удалении фотографий: {str(e)}")

def generate_repost_times(reposts_per_day, start_date, end_date):
    """Генерирует расписание репостов"""
    if not reposts_per_day or not start_date or not end_date:
        return None
    
    # Преобразуем даты в datetime объекты
    start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
    
    # Генерируем времена репостов
    times = []
    if reposts_per_day == 1:
        times = ['10:00']
    elif reposts_per_day == 2:
        times = ['10:00', '15:00']
    else:  # 3 раза
        times = ['10:00', '14:00', '18:00']
    
    return json.dumps(times) 
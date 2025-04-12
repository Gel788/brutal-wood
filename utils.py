import os
import json
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
from app import app, logger
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Проверяет, разрешен ли тип файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_photo(file):
    """Сохраняет загруженную фотографию и возвращает имя файла"""
    try:
        if not file or not allowed_file(file.filename):
            raise ValueError('Недопустимый тип файла')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Проверяем размер файла
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > 5 * 1024 * 1024:  # 5MB max
            raise ValueError('Файл слишком большой')
        
        file.save(filepath)
        return filename
    except Exception as e:
        logger.error(f"Ошибка при сохранении фотографии: {str(e)}")
        raise

def delete_photo(filename):
    """Удаляет фотографию из файловой системы"""
    try:
        if not filename:
            return
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.error(f"Ошибка при удалении фотографии: {str(e)}")
        raise

def init_categories():
    """Инициализирует базовые категории"""
    try:
        from models import Category, db
        
        categories = [
            'Недвижимость',
            'Транспорт',
            'Работа',
            'Услуги',
            'Личные вещи',
            'Для дома и дачи',
            'Бытовая техника',
            'Электроника',
            'Хобби и отдых',
            'Животные'
        ]
        
        for name in categories:
            if not Category.query.filter_by(name=name).first():
                category = Category(name=name)
                db.session.add(category)
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Ошибка при инициализации категорий: {str(e)}")
        raise

def validate_time_slots(time_slots):
    """Валидирует формат временных слотов"""
    try:
        slots = [slot.strip() for slot in time_slots.split(',')]
        for slot in slots:
            if not slot:
                continue
            hours, minutes = map(int, slot.split(':'))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError('Неверный формат времени')
        return True
    except Exception as e:
        logger.error(f"Ошибка при валидации временных слотов: {str(e)}")
        return False

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
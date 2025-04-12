import os
import json
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
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
        return []
    
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            try:
                filename = save_photo(file)
                saved_files.append(filename)
            except Exception as e:
                logger.error(f"Ошибка при сохранении фотографии: {str(e)}")
                continue
    
    return saved_files

def delete_photos(photos):
    """Удаляет список фотографий"""
    if not photos:
        return
    
    for photo in photos:
        try:
            delete_photo(photo)
        except Exception as e:
            logger.error(f"Ошибка при удалении фотографии {photo}: {str(e)}")
            continue

def generate_repost_times(reposts_per_day, start_date, end_date):
    """Генерирует время репостов"""
    if not reposts_per_day or not start_date or not end_date:
        return []
    
    times = []
    current_date = start_date
    while current_date <= end_date:
        for _ in range(reposts_per_day):
            hour = random.randint(9, 21)  # с 9 до 21 часа
            minute = random.randint(0, 59)
            times.append(f"{hour:02d}:{minute:02d}")
        current_date += timedelta(days=1)
    
    return times 
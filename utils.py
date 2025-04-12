import os
import json
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
import logging
import uuid
from models import db, Category

logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """Проверка разрешенных расширений файлов"""
    try:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    except Exception as e:
        logger.error(f"Ошибка при проверке расширения файла: {str(e)}")
        return False

def save_photo(file, upload_folder):
    """Сохранение фотографии"""
    try:
        if not file or not file.filename:
            logger.warning("Попытка сохранить пустой файл")
            return None
            
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            logger.warning(f"Недопустимое расширение файла: {file.filename}")
            return None
            
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Создаем директорию, если она не существует
        os.makedirs(upload_folder, exist_ok=True)
        
        file.save(file_path)
        logger.info(f"Файл успешно сохранен: {unique_filename}")
        return unique_filename
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {str(e)}")
        return None

def delete_photo(filename, upload_folder):
    """Удаление фотографии"""
    try:
        if not filename:
            logger.warning("Попытка удалить файл с пустым именем")
            return False
            
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Файл успешно удален: {filename}")
            return True
        else:
            logger.warning(f"Файл не найден: {filename}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {filename}: {str(e)}")
        return False

def init_categories():
    """Инициализация категорий"""
    try:
        # Проверяем, есть ли уже категории
        if Category.query.first() is not None:
            logger.info("Категории уже инициализированы")
            return
            
        # Создаем базовые категории
        categories = [
            'Недвижимость',
            'Транспорт',
            'Работа',
            'Услуги',
            'Личные вещи',
            'Для дома и дачи',
            'Бытовая электроника',
            'Хобби и отдых'
        ]
        
        for name in categories:
            category = Category(name=name)
            db.session.add(category)
            
        db.session.commit()
        logger.info("Категории успешно инициализированы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации категорий: {str(e)}")
        db.session.rollback()
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
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            try:
                filename = save_photo(file, current_app.config['UPLOAD_FOLDER'])
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
            delete_photo(photo, current_app.config['UPLOAD_FOLDER'])
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
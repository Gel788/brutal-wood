from app import app, db, init_categories, logger

def init_database(drop_existing=False):
    """
    Инициализирует базу данных
    
    Args:
        drop_existing (bool): Если True, удаляет существующие таблицы перед созданием
    """
    try:
        with app.app_context():
            if drop_existing:
                db.drop_all()  # Удаляем все таблицы
            db.create_all()  # Создаем таблицы
            init_categories()  # Инициализируем категории
            logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        raise

if __name__ == '__main__':
    init_database(drop_existing=True)  # При запуске скрипта пересоздаем базу данных 
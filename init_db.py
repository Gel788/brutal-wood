from app import app, db, init_categories, logger

def init_database():
    """Полная переинициализация базы данных"""
    try:
        with app.app_context():
            db.drop_all()  # Удаляем все таблицы
            db.create_all()  # Создаем таблицы заново
            init_categories()  # Инициализируем категории
            logger.info("База данных успешно переинициализирована")
    except Exception as e:
        logger.error(f"Ошибка при переинициализации базы данных: {str(e)}")
        raise

if __name__ == '__main__':
    init_database() 
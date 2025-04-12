from app import app, db, Category

def init_categories():
    """Инициализирует предустановленные категории"""
    categories = [
        {'name': 'Транспорт', 'avito_id': '9'},
        {'name': 'Недвижимость', 'avito_id': '24'},
        {'name': 'Электроника', 'avito_id': '81'},
        {'name': 'Работа', 'avito_id': '111'},
        {'name': 'Услуги', 'avito_id': '99'}
    ]
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Очищаем существующие категории
        Category.query.delete()
        
        # Добавляем новые категории
        for category_data in categories:
            category = Category(
                name=category_data['name'],
                avito_id=category_data['avito_id']
            )
            db.session.add(category)
        
        db.session.commit()
        print("Категории успешно инициализированы")

def init_database():
    try:
        with app.app_context():
            db.drop_all()  # Удаляем все таблицы
            db.create_all()  # Создаем таблицы заново
            init_categories()  # Инициализируем категории
            print("База данных успешно инициализирована!")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {str(e)}")

if __name__ == '__main__':
    init_database() 
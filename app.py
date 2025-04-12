from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import logging
from dotenv import load_dotenv
from models import User, Category, Advertisement
from forms import AdvertisementForm
from utils import save_photo, delete_photo, init_categories

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///avito.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Инициализация расширений
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Создание директории для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_app():
    """Инициализация приложения"""
    with app.app_context():
        db.create_all()
        init_categories()

# Маршруты
@app.route('/')
def index():
    """Главная страница"""
    advertisements = Advertisement.query.order_by(Advertisement.created_at.desc()).all()
    return render_template('index.html', advertisements=advertisements)

@app.route('/add', methods=['GET', 'POST'])
def add_advertisement():
    """Добавление объявления"""
    form = AdvertisementForm()
    if form.validate_on_submit():
        try:
            photos = []
            for photo in form.photos.data:
                if photo:
                    filename = save_photo(photo)
                    photos.append(filename)
            
            advertisement = Advertisement(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                category_id=form.category_id.data,
                photos=photos
            )
            
            db.session.add(advertisement)
            db.session.commit()
            flash('Объявление успешно добавлено!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Ошибка при добавлении объявления: {str(e)}")
            flash('Произошла ошибка при добавлении объявления', 'error')
            db.session.rollback()
    return render_template('add.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_advertisement(id):
    """Редактирование объявления"""
    advertisement = Advertisement.query.get_or_404(id)
    form = AdvertisementForm(obj=advertisement)
    
    if form.validate_on_submit():
        try:
            advertisement.title = form.title.data
            advertisement.description = form.description.data
            advertisement.price = form.price.data
            advertisement.category_id = form.category_id.data
            
            # Обработка новых фотографий
            new_photos = []
            for photo in form.photos.data:
                if photo:
                    filename = save_photo(photo)
                    new_photos.append(filename)
            
            # Удаление старых фотографий
            for photo in advertisement.photos:
                delete_photo(photo)
            
            advertisement.photos = new_photos
            db.session.commit()
            flash('Объявление успешно обновлено!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Ошибка при обновлении объявления: {str(e)}")
            flash('Произошла ошибка при обновлении объявления', 'error')
            db.session.rollback()
    
    return render_template('edit.html', form=form, advertisement=advertisement)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_advertisement(id):
    """Удаление объявления"""
    advertisement = Advertisement.query.get_or_404(id)
    try:
        # Удаление фотографий
        for photo in advertisement.photos:
            delete_photo(photo)
        
        db.session.delete(advertisement)
        db.session.commit()
        flash('Объявление успешно удалено!', 'success')
    except Exception as e:
        logger.error(f"Ошибка при удалении объявления: {str(e)}")
        flash('Произошла ошибка при удалении объявления', 'error')
        db.session.rollback()
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>', methods=['POST'])
def toggle_advertisement(id):
    """Переключение статуса объявления"""
    advertisement = Advertisement.query.get_or_404(id)
    try:
        advertisement.is_active = not advertisement.is_active
        db.session.commit()
        return jsonify({'success': True, 'is_active': advertisement.is_active})
    except Exception as e:
        logger.error(f"Ошибка при переключении статуса объявления: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/categories')
def get_categories():
    """API для получения категорий"""
    categories = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_app()
    app.run(debug=True) 
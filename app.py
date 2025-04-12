from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from models import db, Category, Advertisement
from forms import AdvertisementForm
from utils import allowed_file, save_photo, delete_photo, init_categories

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация для production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///advertisements.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Инициализация расширений
db.init_app(app)
csrf = CSRFProtect(app)

# Создание директории для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_app():
    """Инициализация приложения"""
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        # Инициализируем категории
        init_categories()
    return app

# Инициализация приложения
app = init_app()

@app.route('/')
def index():
    try:
        advertisements = Advertisement.query.order_by(Advertisement.created_at.desc()).all()
        return render_template('index.html', advertisements=advertisements)
    except Exception as e:
        logger.error(f"Ошибка при получении объявлений: {str(e)}")
        flash('Произошла ошибка при загрузке объявлений', 'danger')
        return render_template('index.html', advertisements=[])

@app.route('/add', methods=['GET', 'POST'])
def add_advertisement():
    form = AdvertisementForm()
    if form.validate_on_submit():
        try:
            photos = []
            for file in request.files.getlist('photos'):
                if file and allowed_file(file.filename):
                    filename = save_photo(file)
                    photos.append(filename)
            
            ad = Advertisement(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                address=form.address.data,
                manager_name=form.manager_name.data,
                phone=form.phone.data,
                photos=photos,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                reposts_per_day=form.reposts_per_day.data,
                category_id=form.category_id.data,
                time_slots=form.time_slots.data
            )
            
            db.session.add(ad)
            db.session.commit()
            flash('Объявление успешно добавлено!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при добавлении объявления: {str(e)}")
            flash('Произошла ошибка при добавлении объявления', 'danger')
    return render_template('create_advertisement.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_advertisement(id):
    ad = Advertisement.query.get_or_404(id)
    form = AdvertisementForm(obj=ad)
    
    if form.validate_on_submit():
        try:
            ad.title = form.title.data
            ad.description = form.description.data
            ad.price = form.price.data
            ad.address = form.address.data
            ad.manager_name = form.manager_name.data
            ad.phone = form.phone.data
            ad.start_date = form.start_date.data
            ad.end_date = form.end_date.data
            ad.reposts_per_day = form.reposts_per_day.data
            ad.category_id = form.category_id.data
            ad.time_slots = form.time_slots.data
            
            # Обработка новых фотографий
            for file in request.files.getlist('photos'):
                if file and allowed_file(file.filename):
                    filename = save_photo(file)
                    ad.photos.append(filename)
            
            db.session.commit()
            flash('Объявление успешно обновлено!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при обновлении объявления: {str(e)}")
            flash('Произошла ошибка при обновлении объявления', 'danger')
    
    return render_template('create_advertisement.html', form=form, ad=ad)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_advertisement(id):
    try:
        ad = Advertisement.query.get_or_404(id)
        
        # Удаление фотографий
        for photo in ad.photos:
            delete_photo(photo)
        
        db.session.delete(ad)
        db.session.commit()
        flash('Объявление успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении объявления: {str(e)}")
        flash('Произошла ошибка при удалении объявления', 'danger')
    
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>', methods=['POST'])
def toggle_advertisement(id):
    try:
        ad = Advertisement.query.get_or_404(id)
        ad.is_active = not ad.is_active
        db.session.commit()
        status = 'активировано' if ad.is_active else 'деактивировано'
        flash(f'Объявление успешно {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при изменении статуса объявления: {str(e)}")
        flash('Произошла ошибка при изменении статуса объявления', 'danger')
    
    return redirect(url_for('index'))

@app.route('/api/categories')
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify([{'id': c.id, 'name': c.name} for c in categories])
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {str(e)}")
        return jsonify([]), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
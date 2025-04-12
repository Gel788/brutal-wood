from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from models import db, Category, Advertisement, User
from forms import AdvertisementForm
from utils import allowed_file, save_photo, delete_photo, init_categories
from flask_login import login_required, current_user, login_user, logout_user, LoginManager

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Создание и настройка приложения"""
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
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    with app.app_context():
        # Создаем директорию для загрузок
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Создаем таблицы
        db.create_all()
        # Инициализируем категории
        init_categories()

    return app

# Создание приложения
app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    try:
        advertisements = Advertisement.query.filter_by(is_active=True).order_by(Advertisement.created_at.desc()).all()
        return render_template('index.html', advertisements=advertisements)
    except Exception as e:
        logger.error(f"Ошибка при получении объявлений: {str(e)}")
        flash('Произошла ошибка при загрузке объявлений', 'danger')
        return render_template('index.html', advertisements=[])

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_advertisement():
    form = AdvertisementForm()
    if form.validate_on_submit():
        try:
            # Проверяем существование категории
            category = Category.query.get(form.category_id.data)
            if not category:
                flash('Выбранная категория не существует', 'danger')
                return render_template('create_advertisement.html', form=form)

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
                time_slots=form.time_slots.data,
                user_id=current_user.id
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

@app.route('/edit/<int:ad_id>', methods=['GET', 'POST'])
@login_required
def edit_advertisement(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    if ad.user_id != current_user.id:
        flash('У вас нет прав для редактирования этого объявления', 'danger')
        return redirect(url_for('index'))
    
    form = AdvertisementForm(obj=ad)
    if form.validate_on_submit():
        try:
            # Обновляем основные поля
            ad.title = form.title.data
            ad.description = form.description.data
            ad.price = form.price.data
            ad.category_id = form.category_id.data
            ad.phone = form.phone.data
            ad.address = form.address.data
            ad.time_slots = form.time_slots.data
            
            # Обработка фотографий
            if form.photos.data:
                for photo in form.photos.data:
                    if photo:
                        photo_path = save_photo(photo)
                        if photo_path:
                            ad.photos.append(photo_path)
            
            db.session.commit()
            flash('Объявление успешно обновлено', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении объявления: {str(e)}', 'danger')
            app.logger.error(f'Ошибка при обновлении объявления: {str(e)}')
    
    return render_template('edit_advertisement.html', form=form, ad=ad)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_advertisement(id):
    try:
        ad = Advertisement.query.get_or_404(id)
        
        # Удаление фотографий
        for photo in ad.photos:
            try:
                delete_photo(photo)
            except Exception as e:
                logger.warning(f"Не удалось удалить фотографию {photo}: {str(e)}")
                # Продолжаем удаление даже если не удалось удалить фотографию
        
        db.session.delete(ad)
        db.session.commit()
        flash('Объявление успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении объявления: {str(e)}")
        flash('Произошла ошибка при удалении объявления', 'danger')
    
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>', methods=['POST'])
@login_required
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
        if not categories:
            logger.warning("Список категорий пуст")
            return jsonify([]), 200
        return jsonify([{'id': c.id, 'name': c.name} for c in categories])
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {str(e)}")
        return jsonify({'error': 'Произошла ошибка при получении категорий'}), 500

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    try:
        # Проверяем безопасность имени файла
        if not allowed_file(filename):
            logger.warning(f"Попытка доступа к недопустимому файлу: {filename}")
            return '', 403
            
        # Проверяем существование файла
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            logger.warning(f"Файл не найден: {filename}")
            return '', 404
            
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {filename}: {str(e)}")
        return '', 404

@app.route('/delete_photo/<path:photo_path>', methods=['POST'])
@login_required
def delete_photo(photo_path):
    try:
        # Проверяем, что фотография принадлежит объявлению текущего пользователя
        ad = Advertisement.query.filter(Advertisement.photos.contains([photo_path])).first()
        if not ad or ad.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Нет прав на удаление фотографии'}), 403
        
        # Удаляем фотографию
        delete_photo(photo_path)
        
        # Обновляем список фотографий в объявлении
        ad.photos.remove(photo_path)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при удалении фотографии: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
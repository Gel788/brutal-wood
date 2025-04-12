from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from forms import AdvertisementForm
from utils import save_photos, delete_photos, generate_repost_times
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, FileField, DateField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Email, Optional
from flask_wtf.file import FileAllowed
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///advertisements.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модели
class Ad(db.Model):
    __tablename__ = 'ad'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    photos = db.Column(db.Text)  # JSON строка с путями к фото
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    reposts_per_day = db.Column(db.Integer, default=1)
    repost_times = db.Column(db.Text)  # JSON строка с временем репостов
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    time_slots = db.Column(db.Text)  # JSON строка с временными слотами
    
    category = db.relationship('Category', backref=db.backref('ads', lazy=True))

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    avito_id = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))

# Создаем директорию для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_categories():
    try:
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
        logger.info("Категории успешно инициализированы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации категорий: {str(e)}")
        db.session.rollback()

# Создаем контекст приложения для инициализации базы данных
with app.app_context():
    try:
        db.create_all()
        init_categories()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")

# Маршруты
@app.route('/')
def index():
    print("="*50)
    print("Запрос к главной странице")
    ads = Ad.query.filter_by(is_active=True).all()
    print("Найдено объявлений:", len(ads))
    for ad in ads:
        print(f"Объявление: {ad.title}, ID: {ad.id}, Активно: {ad.is_active}")
    print("="*50)
    return render_template('index.html', ads=ads)

@app.route('/add_ad', methods=['GET', 'POST'])
def add_ad():
    form = AdvertisementForm()
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if request.method == 'POST':
        print("="*50)
        print("POST запрос получен")
        print("Данные формы:", form.data)
        print("Ошибки формы:", form.errors)
        print("Файлы:", request.files)
        print("="*50)
    
    if form.validate_on_submit():
        try:
            print("Форма валидна")
            # Обработка загрузки фотографий
            photo_paths = []
            if form.photos.data:
                for photo in form.photos.data:
                    if photo:
                        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
                        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        photo_paths.append(filename)
            
            # Обработка временных слотов
            time_slots = [slot.strip() for slot in form.time_slots.data.split(',')]
            time_slots = [f"{slot}:00" if len(slot) == 5 else slot for slot in time_slots]  # Добавляем секунды если их нет
            
            # Создание нового объявления
            ad = Ad(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                address=form.address.data,
                manager_name=form.manager_name.data,
                phone=form.phone.data,
                email=form.email.data,
                photos=','.join(photo_paths),
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                reposts_per_day=form.reposts_per_day.data,
                repost_times=generate_repost_times(
                    form.reposts_per_day.data,
                    form.start_date.data.strftime('%Y-%m-%dT%H:%M'),
                    form.end_date.data.strftime('%Y-%m-%dT%H:%M')
                ),
                category_id=form.category_id.data,
                time_slots=','.join(time_slots),
                is_active=True
            )
            
            db.session.add(ad)
            db.session.commit()
            print("Объявление успешно добавлено в базу данных")
            flash('Объявление успешно добавлено', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            print("Ошибка при добавлении объявления:", str(e))
            flash(f'Ошибка при добавлении объявления: {str(e)}', 'danger')
    
    return render_template('create_advertisement.html', form=form, categories=categories)

@app.route('/edit_ad/<int:id>', methods=['GET', 'POST'])
def edit_ad(id):
    ad = Ad.query.get_or_404(id)
    form = AdvertisementForm(obj=ad)
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if request.method == 'POST' and form.validate():
        try:
            # Обновляем данные объявления
            ad.title = form.title.data
            ad.description = form.description.data
            ad.price = form.price.data
            ad.address = form.address.data
            ad.manager_name = form.manager_name.data
            ad.phone = form.phone.data
            ad.email = form.email.data
            ad.start_date = form.start_date.data
            ad.end_date = form.end_date.data
            ad.reposts_per_day = form.reposts_per_day.data
            ad.repost_times = generate_repost_times(
                form.reposts_per_day.data,
                form.start_date.data.strftime('%Y-%m-%dT%H:%M'),
                form.end_date.data.strftime('%Y-%m-%dT%H:%M')
            )
            ad.category_id = form.category_id.data
            ad.time_slots = form.time_slots.data
            ad.is_active = form.is_active.data
            
            # Обновляем фотографии, если загружены новые
            if request.files.getlist('photos'):
                # Удаляем старые фотографии
                delete_photos(ad.photos)
                # Сохраняем новые
                ad.photos = save_photos(request.files.getlist('photos'))
            
            db.session.commit()
            flash('Объявление успешно обновлено', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении объявления: {str(e)}', 'danger')
    
    return render_template('add_ad.html', form=form, ad=ad, categories=categories)

@app.route('/delete_ad/<int:id>', methods=['POST'])
def delete_ad(id):
    ad = Ad.query.get_or_404(id)
    try:
        # Удаляем фотографии
        delete_photos(ad.photos)
        
        db.session.delete(ad)
        db.session.commit()
        flash('Объявление успешно удалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении объявления: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/toggle_ad/<int:id>', methods=['POST'])
def toggle_ad(id):
    ad = Ad.query.get_or_404(id)
    try:
        ad.is_active = not ad.is_active
        db.session.commit()
        status = 'активировано' if ad.is_active else 'деактивировано'
        flash(f'Объявление успешно {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при изменении статуса объявления: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/api/categories')
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

class AdvertisementForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    address = StringField('Адрес', validators=[DataRequired(), Length(max=200)])
    manager_name = StringField('Имя менеджера', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Телефон', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(max=100)])
    photos = FileField('Фотографии', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])
    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата окончания', validators=[DataRequired()])
    reposts_per_day = IntegerField('Количество репостов в день', validators=[NumberRange(min=1, max=10)])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    time_slots = StringField('Временные слоты', validators=[DataRequired()])
    is_active = BooleanField('Активно', default=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
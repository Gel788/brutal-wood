from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from utils import save_photos, delete_photos
import json
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    avito_id = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    parent = db.relationship('Category', remote_side=[id], backref='children')
    advertisements = db.relationship('Advertisement', backref='category', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<Category {self.name}>'

class Advertisement(db.Model):
    __tablename__ = 'advertisements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False, index=True)
    address = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    photos = db.Column(db.JSON, nullable=False, default=list)
    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False, index=True)
    reposts_per_day = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    time_slots = db.Column(db.String(500), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    
    # Связи
    category = db.relationship('Category', backref=db.backref('advertisements', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('advertisements', lazy=True))
    
    def __init__(self, title, description, price, category_id, photos=None, user_id=None):
        self.title = title
        self.description = description
        self.price = price
        self.category_id = category_id
        self.photos = photos or []
        self.user_id = user_id
    
    def __repr__(self):
        return f'<Advertisement {self.title}>'
    
    def save_photos(self, files):
        """Сохраняет фотографии и обновляет список"""
        if not files:
            return
        
        # Удаляем старые фотографии
        if self.photos:
            delete_photos(self.photos)
        
        # Сохраняем новые фотографии
        self.photos = save_photos(files)
    
    @property
    def photos_list(self):
        """Получение списка фотографий"""
        try:
            if isinstance(self.photos, str):
                return json.loads(self.photos)
            return self.photos or []
        except Exception as e:
            logger.error(f"Ошибка при получении списка фотографий: {str(e)}")
            return []
    
    @photos_list.setter
    def photos_list(self, value):
        """Установка списка фотографий"""
        try:
            if isinstance(value, list):
                self.photos = value
            else:
                self.photos = json.dumps(value)
        except Exception as e:
            logger.error(f"Ошибка при установке списка фотографий: {str(e)}")
            self.photos = json.dumps([])
    
    def to_dict(self):
        """Преобразование в словарь"""
        try:
            return {
                'id': self.id,
                'title': self.title,
                'description': self.description,
                'price': self.price,
                'address': self.address,
                'manager_name': self.manager_name,
                'phone': self.phone,
                'photos': self.photos_list,
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'end_date': self.end_date.isoformat() if self.end_date else None,
                'reposts_per_day': self.reposts_per_day,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'category_id': self.category_id,
                'time_slots': self.time_slots,
                'user_id': self.user_id
            }
        except Exception as e:
            logger.error(f"Ошибка при преобразовании в словарь: {str(e)}")
            return {}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>' 
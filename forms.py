from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, DateField, IntegerField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
from datetime import datetime
import re

class AdvertisementForm(FlaskForm):
    title = StringField('Заголовок', validators=[
        DataRequired(message='Введите заголовок'),
        Length(min=5, max=100, message='Заголовок должен быть от 5 до 100 символов')
    ])
    
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Введите описание'),
        Length(min=10, max=1000, message='Описание должно быть от 10 до 1000 символов')
    ])
    
    price = FloatField('Цена', validators=[
        DataRequired(message='Введите цену'),
        NumberRange(min=0, message='Цена не может быть отрицательной')
    ])
    
    address = StringField('Адрес', validators=[
        DataRequired(message='Введите адрес'),
        Length(min=5, max=200, message='Адрес должен быть от 5 до 200 символов')
    ])
    
    manager_name = StringField('Имя менеджера', validators=[
        DataRequired(message='Введите имя менеджера'),
        Length(min=2, max=100, message='Имя должно быть от 2 до 100 символов')
    ])
    
    phone = StringField('Телефон', validators=[
        DataRequired(message='Введите телефон'),
        Length(min=10, max=20, message='Телефон должен быть от 10 до 20 символов')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Введите email'),
        Email(message='Введите корректный email')
    ])
    
    photos = FileField('Фотографии', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения!')
    ])
    
    start_date = DateField('Дата начала', validators=[DataRequired()], default=datetime.now)
    
    end_date = DateField('Дата окончания', validators=[DataRequired()])
    
    reposts_per_day = IntegerField('Количество публикаций в день', 
                                  validators=[DataRequired(), NumberRange(min=1, max=24)],
                                  default=1)
    
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    
    time_slots = StringField('Временные слоты', validators=[DataRequired()])
    
    def validate_time_slots(self, field):
        # Проверяем формат времени (HH:MM)
        time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
        slots = [slot.strip() for slot in field.data.split(',')]
        
        for slot in slots:
            if not time_pattern.match(slot):
                raise ValidationError('Введите время в формате ЧЧ:ММ (например, 09:00)')
    
    def validate_end_date(self, field):
        if field.data <= self.start_date.data:
            raise ValidationError('Дата окончания должна быть позже даты начала')
        
    def validate_start_date(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('Дата начала не может быть в прошлом') 
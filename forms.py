from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, FileField, DateField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
from datetime import datetime
from utils import validate_time_slots

class AdvertisementForm(FlaskForm):
    title = StringField('Заголовок', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=3, max=200, message='Длина заголовка должна быть от 3 до 200 символов')
    ])
    
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=10, max=2000, message='Длина описания должна быть от 10 до 2000 символов')
    ])
    
    price = FloatField('Цена', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        NumberRange(min=0, message='Цена не может быть отрицательной')
    ])
    
    address = StringField('Адрес', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=5, max=200, message='Длина адреса должна быть от 5 до 200 символов')
    ])
    
    manager_name = StringField('Имя менеджера', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=2, max=100, message='Длина имени должна быть от 2 до 100 символов')
    ])
    
    phone = StringField('Телефон', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=5, max=20, message='Длина телефона должна быть от 5 до 20 символов')
    ])
    
    photos = FileField('Фотографии', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Разрешены только изображения форматов PNG, JPG, JPEG, GIF')
    ])
    
    start_date = DateField('Дата начала', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    
    end_date = DateField('Дата окончания', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    
    reposts_per_day = IntegerField('Количество репостов в день', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        NumberRange(min=1, max=10, message='Количество репостов должно быть от 1 до 10')
    ])
    
    category_id = SelectField('Категория', coerce=int, validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    
    time_slots = StringField('Временные слоты', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    
    is_active = BooleanField('Активно', default=True)

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('Дата окончания не может быть раньше даты начала')
    
    def validate_time_slots(self, field):
        if not validate_time_slots(field.data):
            raise ValidationError('Неверный формат времени. Используйте формат HH:MM, разделяя значения запятыми')
    
    def validate_photos(self, field):
        if field.data:
            for file in field.data:
                if file and not file.filename:
                    raise ValidationError('Ошибка загрузки файла') 
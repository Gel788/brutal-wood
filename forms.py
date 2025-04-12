from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, FileField, DateField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Email, ValidationError
from flask_wtf.file import FileAllowed
from datetime import datetime

class AdvertisementForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    address = StringField('Адрес', validators=[DataRequired(), Length(max=200)])
    manager_name = StringField('Имя менеджера', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Телефон', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    photos = FileField('Фотографии', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])
    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата окончания', validators=[DataRequired()])
    reposts_per_day = IntegerField('Количество репостов в день', validators=[NumberRange(min=1, max=10)])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    time_slots = StringField('Временные слоты', validators=[DataRequired()])
    is_active = BooleanField('Активно', default=True)

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('Дата окончания должна быть позже даты начала')

    def validate_time_slots(self, field):
        slots = [slot.strip() for slot in field.data.split(',')]
        for slot in slots:
            try:
                datetime.strptime(slot, '%H:%M')
            except ValueError:
                raise ValidationError('Неверный формат времени. Используйте формат HH:MM') 
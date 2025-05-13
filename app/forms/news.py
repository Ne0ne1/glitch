from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed


# Форма блога
class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[DataRequired()])
    image = FileField('Изображение', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Только изображения!')
    ])
    is_private = BooleanField('Приватная запись')
    submit = SubmitField('Добавить')
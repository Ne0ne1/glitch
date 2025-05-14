from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed


# Форма создания нового чата
class NewChatForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Начать чат')


# Форма отправки сообщения
class MessageForm(FlaskForm):
    text = TextAreaField('Сообщение', validators=[DataRequired()])
    image = FileField('Изображение', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Отправить')

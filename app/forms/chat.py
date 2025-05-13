from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


# Форма чата
class NewChatForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Начать чат')


# Форма сообщения
class MessageForm(FlaskForm):
    text = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')
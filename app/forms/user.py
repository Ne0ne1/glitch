from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, Length

# Форма регистрации
class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=4, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Полное имя')
    about = TextAreaField("О себе")
    submit = SubmitField('Зарегистрироваться')


#Форма Логина
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])  
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
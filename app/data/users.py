import datetime
import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


# Класс пользователя
class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String(50), 
                               unique=True, 
                               index=True, 
                               nullable=False)  # Добавлено новое поле
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String(500), nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String(120), 
                            unique=True, 
                            index=True, 
                            nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String(128), nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, 
                                   default=datetime.datetime.now)
    news = orm.relationship("News", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
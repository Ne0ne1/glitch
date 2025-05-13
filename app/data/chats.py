from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


# Класс чата
class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user1_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    user2_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    
    user1 = orm.relationship('User', foreign_keys=[user1_id])
    user2 = orm.relationship('User', foreign_keys=[user2_id])
    messages = orm.relationship('Message', back_populates='chat') 


# Класс сообщения
class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    text = sa.Column(sa.Text, nullable=True) 
    image = sa.Column(sa.String(255), nullable=True) 
    sender_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    chat_id = sa.Column(sa.Integer, sa.ForeignKey('chats.id'))
    timestamp = sa.Column(sa.DateTime, default=datetime.now)
    
    sender = orm.relationship('User')
    chat = orm.relationship('Chat', back_populates='messages')  
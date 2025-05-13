from flask import Flask, render_template, redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from app.data import db_session
from app.data.users import User
from app.data.news import News
from app.data.chats import Chat, Message
from app.forms.user import RegisterForm, LoginForm
from app.forms.news import NewsForm
from app.forms.chat import NewChatForm, MessageForm
import os
from werkzeug.utils import secure_filename
import uuid
from PIL import Image, ImageOps

app = Flask(__name__, template_folder='app/templates')
csrf = CSRFProtect(app)

# Конфигурация
app.config.update(
    SECRET_KEY='your_very_secret_key_here',
    UPLOAD_FOLDER=os.path.join('static', 'uploads'),
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'webp'},
    IMAGE_TARGET_SIZE=(300, 300), 
    IMAGE_QUALITY=90,           
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

# Создание папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_image(image_path, target_size, quality):
    try:
        img = Image.open(image_path)
        
        # Обрезаем и масштабируем с сохранением пропорций
        img = ImageOps.fit(
            img, 
            target_size,
            method=Image.Resampling.LANCZOS, 
            bleed=0.0,
            centering=(0.5, 0.5)
        )
        # Сохраняем
        img.save(
            image_path,
            'WEBP',
            quality=quality,
            optimize=True,
            method=6  
        )
        
    except Exception as e:
        print(f"Ошибка обработки: {e}")
        raise


# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    try:
        return db_sess.query(User).get(int(user_id))
    finally:
        db_sess.close()


@app.route("/")
def index():
    db_sess = db_session.create_session()
    try:
        if current_user.is_authenticated:
            news = db_sess.query(News).filter(
                (News.user == current_user) | 
                (News.is_private != True)
            ).order_by(News.created_date.desc())
        else:
            news = db_sess.query(News).filter(News.is_private != True)
        return render_template("index.html", news=news)
    finally:
        db_sess.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form, message="Пароли не совпадают")
        
        db_sess = db_session.create_session()
        try:
            if db_sess.query(User).filter(User.username == form.username.data).first():
                return render_template('register.html', form=form, message="Логин занят")
            
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', form=form, message="Email уже используется")
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                name=form.name.data,
                about=form.about.data
            )
            user.set_password(form.password.data)
            
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        finally:
            db_sess.close()
    
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            user = db_sess.query(User).filter(User.username == form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                 message="Неправильный логин или пароль",
                                 form=form)
        finally:
            db_sess.close()
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            news = News(
                title=form.title.data,
                content=form.content.data,
                is_private=form.is_private.data,
                user_id=current_user.id
            )
            
            if form.image.data:
                image = form.image.data
                if allowed_file(image.filename):
                    # Создаем уникальное имя файла
                    filename = secure_filename(image.filename)
                    unique_name = f"{uuid.uuid4()}_{filename}"
                    
                    # Создаем папку uploads, если ее нет
                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)  # Ключевая строка!
                    
                    # Сохраняем файл
                    save_path = os.path.join(upload_folder, unique_name)
                    image.save(save_path)
                    
                    # Сжимаем изображение (если нужно)
                    process_image(save_path, 
                            app.config['IMAGE_TARGET_SIZE'],
                            app.config['IMAGE_QUALITY'])
                    news.image = unique_name
            
            db_sess.add(news)
            db_sess.commit()
            return redirect('/')
        finally:
            db_sess.close()
    return render_template('add_news.html', title='Добавление новости', form=form)


@app.route('/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    try:
        news = db_sess.query(News).filter(News.id == id, 
                                        News.user_id == current_user.id).first()
        if not news:
            return redirect('/')
        
        if form.validate_on_submit():
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        
        form.title.data = news.title
        form.content.data = news.content
        form.is_private.data = news.is_private
        return render_template('add_news.html', 
                             title='Редактирование новости',
                             form=form)
    finally:
        db_sess.close()


@app.route('/delete_news/<int:id>', methods=['POST'])
@login_required
def delete_news(id):
    db_sess = db_session.create_session()
    try:
        news = db_sess.query(News).filter(News.id == id, 
                                       News.user_id == current_user.id).first()
        if news:
            db_sess.delete(news)
            db_sess.commit()
        return redirect('/')
    finally:
        db_sess.close()


@app.route('/chats')
@login_required
def chats_list():
    db_sess = db_session.create_session()
    try:
        chats = db_sess.query(Chat).filter(
            (Chat.user1_id == current_user.id) | 
            (Chat.user2_id == current_user.id)
        ).all()
        return render_template('chats.html', chats=chats)
    finally:
        db_sess.close()


@app.route('/new_chat', methods=['GET', 'POST'])
@login_required
def new_chat():
    form = NewChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            user = db_sess.query(User).filter(User.username == form.username.data).first()
            
            if not user:
                return render_template('new_chat.html', 
                                     form=form,
                                     message="Пользователь не найден")
            
            if user.id == current_user.id:
                return render_template('new_chat.html', 
                                     form=form,
                                     message="Нельзя создать чат с собой")
            
            existing_chat = db_sess.query(Chat).filter(
                ((Chat.user1_id == current_user.id) & (Chat.user2_id == user.id)) |
                ((Chat.user1_id == user.id) & (Chat.user2_id == current_user.id))
            ).first()
            
            if existing_chat:
                return redirect(url_for('chat', chat_id=existing_chat.id))
            
            new_chat = Chat(user1_id=current_user.id, user2_id=user.id)
            db_sess.add(new_chat)
            db_sess.commit()
            return redirect(url_for('chat', chat_id=new_chat.id))
        finally:
            db_sess.close()
    
    return render_template('new_chat.html', form=form)


@app.route('/chat/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def chat(chat_id):
    db_sess = db_session.create_session()
    try:
        chat = db_sess.query(Chat).get(chat_id)
        
        if current_user.id not in [chat.user1_id, chat.user2_id]:
            abort(403)
        
        form = MessageForm()
        if form.validate_on_submit():
            message = Message(
                text=form.text.data,
                sender_id=current_user.id,
                chat_id=chat_id
            )
            db_sess.add(message)
            db_sess.commit()
            return redirect(url_for('chat', chat_id=chat_id))
        
        messages = db_sess.query(Message).filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
        return render_template('chat.html', 
                             chat=chat,
                             messages=messages,
                             form=form)
    finally:
        db_sess.close()


def main():
    db_session.global_init("db/blogs.db")
    app.run(debug=True)


if __name__ == '__main__':
    main()


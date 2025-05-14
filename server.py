from flask import Flask, render_template, redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed
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

# Инициализация Flask приложения
app = Flask(__name__, template_folder='app/templates')
csrf = CSRFProtect(app)  # Защита от CSRF атак

# Конфигурация приложения
app.config.update(
    SECRET_KEY='ABDUL-RAHIM_AND_12_FRIENDS_OF_SHAMIL',
    UPLOAD_FOLDER=os.path.join('static', 'uploads'),  # Папка для загрузки файлов
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'webp'},  # Разрешенные расширения файлов
    IMAGE_TARGET_SIZE=(300, 300),  # Целевой размер изображений
    IMAGE_QUALITY=90,              # Качество сжатия изображений
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # Максимальный размер загружаемого файла (16MB)
)

# Создание папок для загрузок, если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'chat'), exist_ok=True)

def allowed_file(filename):
    """Проверяет, разрешено ли расширение файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_image(image_path, target_size, quality):
    """Обрабатывает изображение: обрезает, масштабирует и сжимает"""
    try:
        img = Image.open(image_path)
        
        # Обрезаем и масштабируем с сохранением пропорций
        img = ImageOps.fit(
            img, 
            target_size,
            method=Image.Resampling.LANCZOS, 
            bleed=0.0,
            centering=(0.5, 0.5)
        
        # Сохраняем обработанное изображение
        img.save(
            image_path,
            'WEBP',
            quality=quality,
            optimize=True,
            method=6)
        
    except Exception as e:
        print(f"Ошибка обработки: {e}")
        raise

# Инициализация Flask-Login для аутентификации пользователей
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Страница для входа


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя для Flask-Login"""
    db_sess = db_session.create_session()
    try:
        return db_sess.query(User).get(int(user_id))
    finally:
        db_sess.close()


@app.route("/")
def index():
    """Главная страница с новостями"""
    db_sess = db_session.create_session()
    try:
        if current_user.is_authenticated:
            # Для авторизованных пользователей показываем их и публичные новости
            news = db_sess.query(News).filter(
                (News.user == current_user) | 
                (News.is_private != True)
            ).order_by(News.created_date.desc())
        else:
            # Для гостей только публичные новости
            news = db_sess.query(News).filter(News.is_private != True)
        return render_template("index.html", news=news)
    finally:
        db_sess.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form, message="Пароли не совпадают")
        
        db_sess = db_session.create_session()
        try:
            # Проверка на уникальность логина
            if db_sess.query(User).filter(User.username == form.username.data).first():
                return render_template('register.html', form=form, message="Логин занят")
            
            # Проверка на уникальность email
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', form=form, message="Email уже используется")
            
            # Создание нового пользователя
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
    """Авторизация пользователя"""
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
    """Выход из системы"""
    logout_user()
    return redirect("/")


@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    """Добавление новости"""
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
            
            # Обработка загружаемого изображения
            if form.image.data:
                image = form.image.data
                if allowed_file(image.filename):
                    # Генерация уникального имени файла
                    filename = secure_filename(image.filename)
                    unique_name = f"{uuid.uuid4()}_{filename}"
                    
                    # Создание папки для загрузок, если ее нет
                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Сохранение файла
                    save_path = os.path.join(upload_folder, unique_name)
                    image.save(save_path)
                    
                    # Обработка изображения
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
    """Редактирование новости"""
    form = NewsForm()
    db_sess = db_session.create_session()
    try:
        # Получаем новость, принадлежащую текущему пользователю
        news = db_sess.query(News).filter(News.id == id, 
                                        News.user_id == current_user.id).first()
        if not news:
            return redirect('/')
        
        if form.validate_on_submit():
            # Обновление данных новости
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        
        # Заполнение формы текущими данными
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
    """Удаление новости"""
    db_sess = db_session.create_session()
    try:
        # Удаляем только новости, принадлежащие текущему пользователю
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
    """Список чатов пользователя"""
    db_sess = db_session.create_session()
    try:
        # Получаем все чаты, где пользователь является участником
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
    """Создание нового чата"""
    form = NewChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            # Ищем пользователя по имени
            user = db_sess.query(User).filter(User.username == form.username.data).first()
            
            if not user:
                return render_template('new_chat.html', 
                                     form=form,
                                     message="Пользователь не найден")
            
            # Нельзя создать чат с самим собой
            if user.id == current_user.id:
                return render_template('new_chat.html', 
                                     form=form,
                                     message="Нельзя создать чат с собой")
            
            # Проверяем, существует ли уже чат между этими пользователями
            existing_chat = db_sess.query(Chat).filter(
                ((Chat.user1_id == current_user.id) & (Chat.user2_id == user.id)) |
                ((Chat.user1_id == user.id) & (Chat.user2_id == current_user.id))
            ).first()
            
            if existing_chat:
                return redirect(url_for('chat', chat_id=existing_chat.id))
            
            # Создаем новый чат
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
    """Страница чата с сообщениями"""
    db_sess = db_session.create_session()
    try:
        chat = db_sess.query(Chat).get(chat_id)
        
        # Проверяем, является ли пользователь участником чата
        if current_user.id not in [chat.user1_id, chat.user2_id]:
            abort(403)
        
        form = MessageForm()
        if form.validate_on_submit():
            # Создание нового сообщения
            message = Message(
                text=form.text.data,
                sender_id=current_user.id,
                chat_id=chat_id
            )
            
            # Обработка изображения в сообщении
            if form.image.data:
                image = form.image.data
                if allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    unique_name = f"{uuid.uuid4()}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'chat', unique_name)

                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    image.save(save_path)

                    print(">>> Файл сохранён успешно?")
                    print(">>> message.image:", os.path.join('chat', unique_name))

                    # Обработка изображения
                    process_image(save_path, 
                                  app.config['IMAGE_TARGET_SIZE'],
                                  app.config['IMAGE_QUALITY'])
                    
                    message.image = f"chat/{unique_name}"
            
            db_sess.add(message)
            db_sess.commit()
            return redirect(url_for('chat', chat_id=chat_id))
        
        # Получаем все сообщения чата
        messages = db_sess.query(Message).filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
        return render_template('chat.html', 
                             chat=chat,
                             messages=messages,
                             form=form)
    finally:
        db_sess.close()


@app.route('/post/<int:post_id>')
def get_post_modal(post_id):
    """Получение модального окна с постом"""
    db_sess = db_session.create_session()
    try:
        post = db_sess.query(News).get(post_id)
        if not post:
            return "Пост не найден", 404
        return render_template("post_modal.html", post=post)
    finally:
        db_sess.close()


def main():
    """Запуск приложения"""
    db_session.global_init("db/blogs.db")
    app.run(debug=True)


if __name__ == '__main__':
    main()
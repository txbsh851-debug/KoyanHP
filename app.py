from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect
from datetime import datetime
from datetime import timedelta, timezone
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_bootstrap import Bootstrap

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"  # SQLite database
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'

# 未ログインユーザーにメッセージ表示
def localize_callback(*args, **kwarg):
    return 'このページにアクセスするには、ログインが必要です'
login_manager.localize_callback = localize_callback

# アップロードするフォルダのパスを設定
UPLOAD_FOLDER = "static/img"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# フォルダが存在しない場合は作成する
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 時間を取得
now = datetime.now()

formatted_datetime = now.strftime("%Y-%m-%d %H:%M")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    create_at = db.Column(db.String(30), nullable=False, default=formatted_datetime)
    img_name = db.Column(db.String(100), nullable=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        posts = Post.query.all()
        return render_template("index.html", posts=posts)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    # URLでhttp://127.0.0.1:5000/uploadを指定したときはGETリクエストとなるのでこっち
    if request.method == "GET":
        return render_template("create.html")
    # formでsubmitボタンが押されるとPOSTリクエストとなるのでこっち
    elif request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        file = request.files["file"]
        filename = file.filename
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        post = Post(title=title, body=body, img_name=save_path)
        db.session.add(post)
        db.session.commit()
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # ユーザー名とパスワードの受け取り
        username = request.form.get("username")
        password = request.form.get("password")
        # データベースから情報を取得
        user = User.query.filter_by(username=username).first()
        # 入力パスワードとデータベースが一致しているか確認
        if check_password_hash(user.password, password=password):
            # 一致していれば、ログインさせて、管理画面へリダイレクト
            login_user(user)
            return redirect("/")
        else:
            # 間違ってる場合、エラー分と共にログイン画面へリダイレクト
            return redirect("/login", msg="ユーザー名/パスワードが違います")
    elif request.method == "GET":
        return render_template("login.html", msg="")


def logout():
    logout_user()
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
@login_required
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_pass = generate_password_hash(password)
        user = User(username=username, password=hashed_pass)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    elif request.method == "GET":
        return render_template("signup.html")


@app.route("/<int:id>/update", methods=["GET", "POST"])
@login_required
def update(id):
    post = Post.query.get(id)
    if request.method == "GET":
        return render_template("update.html", post=post)
    else:
        post.title = request.form.get("title")
        post.body = request.form.get("body")

        db.session.commit()
        return redirect("/")


@app.route("/<int:id>/delete", methods=["GET"])
@login_required
def delete(id):
    post = Post.query.get(id)

    db.session.delete(post)
    db.session.commit()
    return redirect("/")

@app.route("/contact", methods=["GET"])
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run()

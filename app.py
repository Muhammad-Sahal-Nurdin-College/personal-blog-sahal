import os
from dotenv import load_dotenv
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from datetime import date
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, url_for, make_response, jsonify
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from forms import CommentForm, CreatePostForm, LoginForm, RegisterForm

from git_handle import git_push
from tables import BlogPost, Comment, User, db



# Muat environment variables dari file .env
load_dotenv()

app = Flask(__name__,instance_relative_config=True)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
# Serializer untuk membuat dan memverifikasi token
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# ==================== KONFIGURASI FLASK-MAIL ==================== #
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Sahal\'s Blog', os.getenv('MAIL_USERNAME'))

mail = Mail(app)
# ============================================================= #

# interacting with CkEditor
ckeditor = CKEditor(app)
app.config["CKEDITOR_PKG_TYPE"] = "standard-all"
app.config["CKEDITOR_ENABLE_CODESNIPPET"] = True

# Bootstrap
Bootstrap(app)

# Connect to DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


# Gravatar!
gravatar = Gravatar(
    app,
    size=100,
    rating="g",
    default="retro",
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None,
)

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)

# Flask Login Functions
@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Global Variables?
@app.context_processor
def get_year():
    return dict(year=date.today().year)


@app.route("/")
def home():
    # Ambil semua postingan dan urutkan berdasarkan tanggal terbaru (best practice)
    # Ini akan mengembalikan daftar kosong jika tidak ada post, tanpa menyebabkan error
    all_blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    
    # Kirim daftar postingan ke template
    # Jika all_blog_posts kosong, perulangan for di template tidak akan berjalan
    return render_template("index.html", all_posts=all_blog_posts)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ================= LOGIN / REGISTER ============================== #
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email sudah terdaftar! Silakan login.")
            return redirect(url_for("login"))

        password = generate_password_hash(
            form.password.data, method="pbkdf2:sha256", salt_length=8
        )
        # Buat user dengan status is_verified = False
        new_user = User(
            email=email, 
            password=password, 
            name=form.name.data,
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # === KIRIM EMAIL VERIFIKASI ===
        # Buat token (berlaku selama 1 jam / 3600 detik)
        token = serializer.dumps(email, salt='email-verification-salt')
        # Buat link verifikasi
        verification_url = url_for('verify_email', token=token, _external=True)
        # Buat pesan email
        msg = Message(
            subject="Verifikasi Akun Sahal's Blog",
            recipients=[email],
            html=f"<p>Terima kasih telah mendaftar! Klik link di bawah ini untuk memverifikasi akun Anda:</p>"
                 f"<p><a href='{verification_url}'>{verification_url}</a></p>"
                 f"<p>Jika Anda tidak merasa mendaftar, abaikan email ini.</p>"
        )
        mail.send(msg)
        # ===============================

        flash("Pendaftaran berhasil! Silakan cek email Anda untuk verifikasi akun.", "info")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route('/verify/<token>')
def verify_email(token):
    try:
        # Verifikasi token dengan masa berlaku 1 jam (3600 detik)
        email = serializer.loads(token, salt='email-verification-salt', max_age=3600)
    except SignatureExpired:
        flash("Link verifikasi telah kedaluwarsa. Silakan daftar ulang.", "danger")
        return redirect(url_for('register'))
    except BadSignature:
        flash("Link verifikasi tidak valid.", "danger")
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first_or_404()
    
    if user.is_verified:
        flash("Akun sudah diverifikasi. Silakan login.", "info")
    else:
        user.is_verified = True
        db.session.commit()
        flash("Akun Anda telah berhasil diverifikasi! Silakan login.", "success")
        
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash("Email tidak terdaftar di database kami!")
            return render_template("login.html", form=form)

        # Cek apakah password cocok
        if check_password_hash(pwhash=user.password, password=form.password.data):
            
            # === TAMBAHKAN PENGECEKAN INI ===
            if not user.is_verified:
                flash("Akun Anda belum diverifikasi. Silakan cek email Anda.", "warning")
                return redirect(url_for('login'))
            # ===============================

            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Password salah, silakan coba lagi!")
            return render_template("login.html", form=form)
            
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


# ====================== ADDING / SHOWING / EDITING /  DELETING POSTS ============= #
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    all_comments = db.session.query(Comment).all()[::-1]
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.body.data,
                author=current_user,
                author_id=current_user.id,
                post=requested_post,
                post_id=post_id,
            )
            db.session.add(new_comment)
            db.session.commit()

            return redirect(url_for("show_post", post_id=post_id))

        else:
            flash("You need to be logged in to make a comment!")
            return redirect(url_for("login"))

    return render_template(
        "post.html", post=requested_post, form=form, all_comments=all_comments
    )


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_post)
        db.session.commit()

        git_push("Added a post -- autobackup")

        return redirect(url_for("home"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()

        git_push("Edited a post -- autobackup")

        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()

    git_push("Deleted a post -- auto-backup")

    return redirect(url_for("home"))


@app.route("/set-cookie-consent")
def set_cookie_consent():
    # Buat response JSON sederhana
    response = make_response(jsonify(message="Cookie consent set"))
    
    # Set cookie bernama 'cookie_consent' dengan nilai 'true'
    # max_age diatur dalam detik. 31536000 detik = 1 tahun.
    response.set_cookie('cookie_consent', 'true', max_age=60) 
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
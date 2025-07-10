from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Email
from flask_wtf.file import FileField, FileAllowed 



##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Judul Postingan Blog ", validators=[DataRequired()])
    subtitle = StringField("Tambahkan Subjudul", validators=[DataRequired()])
    img_url = StringField("Gambar URL Blog", validators=[DataRequired(), URL()])
    body = CKEditorField("Konten Blog", validators=[DataRequired()])
    submit = SubmitField("Publikasikan")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Kata Sandi", validators=[DataRequired()])
    name = StringField("Nama", validators=[DataRequired()])
    submit = SubmitField("Daftar Sekarang")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Kata Sandi", validators=[DataRequired()])
    submit = SubmitField("Masuk")


class CommentForm(FlaskForm):
    body = CKEditorField("Komentar", validators=[DataRequired()])
    submit = SubmitField("Tambah Komentar")
    
class GeneralRecommendationForm(FlaskForm):
    title = StringField("Judul Rekomendasi")
    notes = TextAreaField("Catatan Tambahan (opsional)")
    file = FileField("Lampirkan File", validators=[
        FileAllowed(['pdf', 'docx', 'zip', 'jpg', 'png'], 'File tidak didukung!')
    ])
    submit = SubmitField("Upload dan Kirim ke Admin")
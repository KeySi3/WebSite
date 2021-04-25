from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, \
    BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()], id="emailf")
    password = PasswordField('Пароль', validators=[DataRequired()], id="passwordf")
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()], id="passwordf2")
    ok_email = SubmitField('Отправить код')
    code = StringField('Код подтверждения', validators=[DataRequired()], id='code_sub')
    submit = SubmitField('Зарегистрироваться', id='okbtn')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()], id='name')
    password = PasswordField('Пароль', validators=[DataRequired()], id='password')
    remember_me = BooleanField('Запомнить меня', id='checkbox')
    submit = SubmitField('Войти', id='enter')
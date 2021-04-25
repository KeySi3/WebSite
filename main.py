import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import choice
from sched import scheduler
from tkinter import *
from tkinter import messagebox
import threading
import requests
import schedule
import xlrd
import xlsxwriter
from flask import Flask, render_template, jsonify, request, flash, send_file
from flask_login import LoginManager, login_user, current_user, logout_user, \
    login_required
import sys

from flask_ngrok import run_with_ngrok
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect, secure_filename
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data import db_session
from data.passwords import Password
from forms.user import RegisterForm
from forms.user import LoginForm
import os
import sqlite3
import json
from scripts.sorting import *
from mail import send_mail
from pprint import pprint
from datetime import timedelta

# папка для работы с загружными файлами
path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'TEACHER_HELPER_PROJECT'
run_with_ngrok(app)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'xlsx', 'jpg', 'png'}

REMINDINGS_USERS = {}
times = {}
SEND_OR_NOT = {}


# tasks = {email: {id: tasK_1, id2; tsk2}}

def stuff_mail(email, theme,
               text):  # отправка паролей для входа и проверочных кодов,
    global times, REMINDINGS_USERS
    message = MIMEMultipart()
    message["Subject"] = theme
    message["From"] = 'nicolaynemov007@yandex.ru'
    body = text
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
        server.login('nicolaynemov007@yandex.ru', 'Shwabra26')
        server.sendmail(message['from'], email, message.as_string())
        b = True
    except Exception as e:
        b = e.args
    return b


def allowed_file(filename):
    return filename.split('.')[-1] in ALLOWED_EXTENSIONS


@app.route("/remindings/deleting", methods=["POST"])
def delete_reminding():
    global times, REMINDINGS_USERS, SEND_OR_NOT
    if request.method == 'POST':
        date = [i.split("+-+") for i in
                request.form["date"].split("___===___")]
        email = request.form["date"]
        for data in [x[0] for x in date]:
            for deliting in times[data]:
                ok_mas = []
                for user in REMINDINGS_USERS[deliting[0]]:
                    if user[0] != data or user[1] != deliting[1] or user[2] != \
                            deliting[2]:
                        ok_mas.append(user)
                REMINDINGS_USERS[deliting[0]] = ok_mas.copy()
        return "deleted"
    return "Не удалось удалить напоминание"


@app.route("/remindings/<email>", methods=["GET", "POST"])
def return_data(email):
    result = {}
    global REMINDINGS_USERS
    if email in REMINDINGS_USERS:
        result["Дате и времени"] = sort_by_date_dates(REMINDINGS_USERS[email],
                                                      0)
        result["Названию"] = sorted(REMINDINGS_USERS[email],
                                    key=lambda x: x[1])
        result["look_data"] = [''.join([str(i) for i in j[:-1]]).lower() for j
                               in REMINDINGS_USERS[email]]

        return jsonify(result)
    result["Дате и времени"] = []
    return jsonify(result)


# tasks = {email: {id: tasK_1, id2; tsk2}}


@app.route("/remindings/adding", methods=["POST", "GET"])
def add_datas():
    global REMINDINGS_USERS, remind_data, SEND_OR_NOT, times
    if request.method == 'POST':
        date = request.form["date"].strip()
        date = date.replace("T", " ")
        year, month, day = date.split()[0].split("-")
        time = date.split()[1]
        date = f"{day}.{month}.{year} {time}"
        t1_dt = datetime.strptime(date, "%d.%m.%Y %H:%M")
        t2_dt = datetime.now()
        t = t1_dt - t2_dt
        if t < timedelta(seconds=60):
            return "Слишком маленький временной промежуток"
        if t > timedelta(days=7):
            return "Слишком большой временной промежуток"
        email = request.form["email"].strip()
        theme = request.form["theme"].strip()
        text = request.form["text"].strip()
        if email not in REMINDINGS_USERS:
            REMINDINGS_USERS[email] = [[date, theme, text]]
        else:
            REMINDINGS_USERS[email].append([date, theme, text])
        if date not in times:
            times[date] = [[email, theme, text]]
        else:
            times[date].append([email, theme, text])
        if email not in SEND_OR_NOT:
            SEND_OR_NOT[email] = True
    return ""


@app.route('/add_account/<email>', methods=['POST'])
def upload_file(email):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            js = request.json()
            flash('No file selected for uploading')

            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            (add_class(email, f"{filename}", request.form["name"],
                       request.form["cap"]))
            flash('File successfully uploaded')
            return redirect(f"/classes/{email}")
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return "error"


# автоизация
login_manager = LoginManager()
login_manager.init_app(app)
# global
code = {}


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Password).get(user_id)


def main():
    db_session.global_init("db/passwords.db")
    app.run()


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/sendmail/<email>/", methods=['POST'])
def sendpismo(email):
    if request.method == 'POST':
        text = request.form["text"]
        theme = request.form["theme"]
        getters = request.form["getters"]
        a = []
        if 'file' in request.files:
            file = request.files["file"]
            filename = secure_filename(file.filename)
            if not os.path.isdir("files_for_sending"):
                os.mkdir("files_for_sending")
            file.save(os.path.join("files_for_sending", filename))
            a = [os.path.join("files_for_sending", filename)]

        getters = [i[i.rindex('(') + 1: -1] for i in getters.split('\n')]
        send_mail(theme=theme, text=text, files=a, emails=getters)
        if a:
            os.remove(os.path.join("files_for_sending", filename))
    return "ok"


@app.route('/feedback/<email>')
def feedback(email):
    return render_template('feedback.html', title='Обратная связь', nick=email)


@app.route('/send/<email>/<getters>', methods=['GET'])
def send(email, getters):
    people = getters.split("---")[:-1]
    fl = []
    for i in people:
        a = i.split('+-+')
        fl.append(f"{a[0]} {a[1]} ({a[2]})")
    people = '\n'.join(fl)
    return render_template('send.html', title='Рассылка', person=people,
                           nick=email)


@login_required
@app.route('/mainwindow/<login>', methods=['GET', 'POST'])
def mainwindow(login):
    result = workwindow(login)
    c = result["classes_names"]
    if c:
        student = [['-'] + ["Value"] * 7 for i in range(100)]
    else:
        student = []
    length = len(student)

    return render_template('mainmenu.html', title='Помощник учителя',
                           classes=c, students=student, a=length, nick=login)


@app.route("/", methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(Password).filter(
            Password.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f'/mainwindow/{form.email.data}')
        return render_template('index.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('index.html', title='Авторизация', form=form)


@app.route('/classes/<nick>')
def classes(nick):
    c = [["-", i] for i in workwindow(nick)["classes_names"]]
    length = len(c)
    return render_template('classes.html', title='Работа с классами',
                           classes=c, a=length, nick=nick)


# регистрация
@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        password = form.password.data
        user_code = form.code.data
        form.code.data = ''
        level = password_level(password)
        if not level[0]:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message=level[1])
        if password != form.password_again.data:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают"
                                           "")
        db_sess = db_session.create_session()
        if db_sess.query(Password).filter(
                Password.email == form.email.data).first():
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if user_code != code[form.email.data]:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Введён неверный код")

        user = Password(
            email=form.email.data,
            hashed_password=form.password.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        # создание рабочей папки для аккаунта
        os.mkdir(f'db/accounts/{form.email.data}')
        with sqlite3.connect("classes.db") as con:
            pass
        with open(f'db/accounts/{form.email.data}' + "/able_classes.json", "w",
                  encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
        with open(f'db/accounts/{form.email.data}' + "/info.json", "w",
                  encoding="utf-8") as f:
            json.dump([str(datetime.now().strftime("%d.%m.%Y %H:%M")), form.email.data, str(datetime.now().strftime("%d.%m.%Y"))], f, ensure_ascii=False)
        with open(f'db/accounts/{form.email.data}' + "/links.json", "w",
                  encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
        with open(f'db/accounts/{form.email.data}' + "/remindings.json", "w",
                  encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)
        with open(f'db/accounts/{form.email.data}' + "/notes.json", "w",
                  encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)

        return redirect('/')
    return render_template('registration.html', title='Регистрация', form=form)

@app.route("/app_reistration", methods=["POST"])
def app_registration():
    if request.method == 'POST':
        pass


@app.route('/code/<email>/<password>', methods=["POST"])
def stuff_mail_2(email,
                 password):  # отправка паролей для входа и проверочных кодов,

    to, password = email, password
    message = MIMEMultipart()
    message["Subject"] = "Проверочный код"
    message["From"] = 'nicolaynemov007@yandex.ru'
    code[to] = str(choice(range(1000, 10000)))
    text = f'''Спасибо, что зарегестрировались в нашей системе "Помощник учителя" !''' + '\n'
    text += f'Ваш никнейм: {to}' + '\n'
    text += f'Ваш пароль: {password}' + '\n'
    text += f'Код подтверждения регистрации: {code[to]}' + '\n' * 2
    text += 'С уважением, разработчики.'
    body = text
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
        server.login('nicolaynemov007@yandex.ru', 'Shwabra26')
        server.sendmail(message['from'], to, message.as_string())
        b = True
    except Exception as e:
        b = False
    return jsonify({"result": b})


# логические функции
def password_level(password):
    if len(password) < 8:
        return False, "Пароль короче 8 символов"
    letters, numbers, up = False, False, False
    for i in password:
        if i.lower() == i and i.isalpha():
            letters = True
        if ord(i) in range(48, 58):
            numbers = True
        if i.upper() == i and ord(i) not in range(48, 58):
            up = True
    if letters and numbers and up:
        return True, 'Ok'
    elif letters and numbers and not up:
        return False, "Добавьте в пароль заглавных букв"
    elif letters and up and not numbers:
        return False, "Добавьтев пароль цифр"
    elif numbers and up and not letters:
        return False, "Добавьте в пароль строчных букв"
    elif numbers and not letters and not up:
        return False, "Добавьтев пароль  букв разных регистров"
    elif letters and not numbers and not up:
        return False, "Добавьте в пароль цифр и заглавных букв"
    else:
        return False, "Добавьте в пароль прописных букв и цифр"


# функция возвррата json_ответа
@app.route('/json_info/<email>', methods=["POST"])
def json_answer(email):
    return jsonify(workwindow(email))


def workwindow(email):
    # print(os.getcwd())
    result = {}
    with open(f"db/accounts/{email}" + '/able_classes.json',
              encoding="utf-8") as classes:
        classes_names = json.load(classes)
    classes_names.sort()
    # словарь для сортировки
    sorting_keys = [{"Фамилии": (srname, False)}, {"Имени": (name, False)},
                    {"Дате рождения": (date, False)},
                    {"Полу (мальчики)": (male, False)},
                    {"Полу (девочки)": (female, False)},
                    {"ФамилииR": (srname, True)},
                    {"ИмениR": (name, True)}, {"Дате рожденияR": (date, True)},
                    {"Полу (мальчики)R": (male, True)},
                    {"Полу (девочки)R": (female, True)}]
    result["classes_names"] = classes_names
    for clas in classes_names:
        result[clas] = {}
        with sqlite3.connect(f"db/accounts/{email}/" + "classes.db") as con:
            cur = con.cursor()
            vals = cur.execute(
                """SELECT * FROM '{}'""".format(clas)).fetchall()
        for sort_key in sorting_keys:
            key, func = list(sort_key.items())[0]
            result[clas][key] = list(func[0](vals, func[1]))
            result[clas]["look_data"] = [''.join(str(student)).lower() for
                                         student
                                         in vals]

    return result


def add_class(email, file, name, cap):
    cap = int(cap != "true")
    con = sqlite3.connect(f"db/accounts/{email}/" + "classes.db")
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS'{}'
                          (фамилия text, имя text, дата_рождения time,
                           пол text, email text, телефон text, родтель text)
                       """.format(name))
    con.commit()
    con.close()
    ## конец работы с БД

    # try:
    rb = xlrd.open_workbook(f"uploads/{file}")

    sheet = rb.sheet_by_index(0)
    vals = [[str(i) for i in list(sheet.row_values(rownum))] for rownum in
            range(sheet.nrows)][:]
    for i in range(len(vals)):
        a = []
        for j in range(7):
            if vals[i][j]:
                a.append(vals[i][j])
            else:
                a.append('Не определено')
        vals[i] = tuple(a)

    with open(f"db/accounts/{email}/" + "able_classes.json", "r",
              encoding="utf-8") as f:
        previous_lits = json.load(f)
    previous_lits.append(name)
    # print(previous_lits)
    with open(f"db/accounts/{email}/" + "able_classes.json", "w",
              encoding="utf-8") as f:
        json.dump(sorted(list(set(previous_lits))), f, ensure_ascii=False)

    ## работа с БД
    con = sqlite3.connect(f"db/accounts/{email}/" + "classes.db")
    cur = con.cursor()
    cur.executemany(
        "INSERT INTO" + f""" '{name}'""" + "VALUES (?,?,?,?,?,?,?)",
        vals)
    con.commit()
    con.close()
    os.remove(f"uploads/{file}")
    return True


@app.route('/about/<email>')
def about(email):
    """c = [['-', '10Б'], ['-', '10Г'], ['-', '10Д']]
    length = len(c)"""
    return render_template('about.html', title='Помощь в работе', nick=email)


@app.route("/class_deleting/<email>/<password>/<classname>",
           methods=["POST", "GET"])
def delete_class(email, password, classname):
    with sqlite3.connect("db/passwords.db") as con:
        cur = con.cursor()
        check_data = [i[0] for i in cur.execute(
            'SELECT hashed_password from passwords where email= "{}"'.format(
                email)).fetchall()][0]
    if not check_password_hash(check_data, password):
        return "Неверный пароль"

    con = sqlite3.connect(f"db/accounts/{email}/" + "classes.db")
    cur = con.cursor()
    cur.execute("""DROP TABLE '{}';""".format(classname))

    con.commit()
    con.close()
    with open(f"db/accounts/{email}/" + 'able_classes.json',
              encoding="utf-8") as classes:
        classes_names = json.load(classes)
    del classes_names[classes_names.index(classname)]

    with open(f"db/accounts/{email}/" + 'able_classes.json', "w",
              encoding="utf-8") as classes:
        json.dump(classes_names, classes, ensure_ascii=False)

    return ""


@app.route("/exporting/<email>/<name>/<filename>/<cap>",
           methods=['POST', 'GET'])
def exporting(email, name, filename, cap):
    main_ak = email
    main_name = name
    main_file = filename
    ## работа с БД
    cap = cap == "true"

    con = sqlite3.connect(f"db/accounts/{email}/" + "classes.db")
    command = f"""SELECT * FROM '{name}'"""
    cur = con.cursor()
    data = cur.execute(
        command).fetchall()
    con.close()
    ## конец аботы с БД
    if cap:
        count = 1
    else:
        count = 0
    if not os.path.isdir("exporting"):
        os.mkdir("exporting")

    workbook = xlsxwriter.Workbook(f'exporting/{filename}.xlsx')
    worksheet = workbook.add_worksheet()
    if count:
        worksheet.write(0, 0, 'Имя')
        worksheet.write(0, 1, 'Фамилия')
        worksheet.write(0, 2, 'Дата рождения')
        worksheet.write(0, 3, 'Пол')
        worksheet.write(0, 4, 'Email')
        worksheet.write(0, 5, 'Телефон')
        worksheet.write(0, 6, 'Родитель')
    for row, (name, srname, date, pol, email, phone, parent) in enumerate(
            data):
        worksheet.write(row + count, 0, name)
        worksheet.write(row + count, 1, srname)
        worksheet.write(row + count, 2, date)
        worksheet.write(row + count, 3, pol)
        worksheet.write(row + count, 4, email)
        worksheet.write(row + count, 5, phone)
        worksheet.write(row + count, 6, parent)
    workbook.close()

    send_mail("Экспорт класса",
              f"Экспорт класса {main_name} в таблицу {filename} успешно произведён",
              [f"exporting/{filename}.xlsx"], [main_ak])
    return jsonify({"result": "Письмо с файлом отправлено на Вашу почту"})


@app.route('/links/<email>')
def links(email):
    link = [['-'] + ["Value", "Value", "Value"] for i in range(100)]
    length = 100
    return render_template('links.html', title='Ссылки', rem=link, a=length,
                           nick=email)


@app.route('/notes/<email>')
def notes(email):
    note = [['-'] + ["Value", "Value"] for i in range(100)]
    length = 100
    data = window_search_data(email, "notes")
    if len(data["Дате и времени"]) <= 12:
        number = 15
    else:
        number = len(data["Дате и времени"]) + 3
    return render_template('notes.html', title='Заметки', rem=note, a=length,
                           nick=email, number=number)


@app.route("/watch/<title>/<text>", methods=["POST", "GET"])
def showtext(title, text):
    return render_template('textshower.html', title=title,
                           text=text.replace("+-+", ' '))


@app.route("/adddata/<email>", methods=["POST", "GET"])
def addata(email):
    if request.method == 'POST':
        name = request.form["name"]
        body = request.form["body"]
        add_type = request.form["type"]
        with open(f"db/accounts/{email}/{add_type}.json", "r",
                  encoding="utf-8") as f:
            a = json.load(f)
        a.append([name, str(datetime.now().strftime("%d.%m.%Y %H:%M")), body])
        with open(f"db/accounts/{email}/{add_type}.json", "w",
                  encoding="utf-8") as f:
            json.dump(a, f)
    return "ok"


@app.route("/get_datas/<email>/<type>", methods=["POST", "GET"])
def get_links_or_notes(email, type):
    with open(f"db/accounts/{email}/{type}.json", "r", encoding="utf-8") as f:
        a = json.load(f)
    result = {}
    result["Дате и времени"] = sort_by_date_dates(a)
    result["Названию"] = sorted(a, key=lambda x: x[0])
    result["look_data"] = [''.join([str(i) for i in j]).lower() for j in a]
    return jsonify(result)


@app.route("/remind/<email>", methods=["POST", "GET"])
def remindings(email):
    """if (reminds[0][0] != "None"):
        reminds = [["-"] + list(i) for i in reminds]
    else:
        reminds = []"""

    reminds = [['-'] + ["Value", "Value"] for i in range(100)]
    length = 100
    return render_template('remind.html', title='Напоминания', rem=reminds,
                           a=length, nick=email, number=15)


@app.route("/send_or_not/<email>", methods=["GET"])
def send_or_not(email):
    global SEND_OR_NOT
    if email not in SEND_OR_NOT:
        return "true"
    if SEND_OR_NOT[email]:
        return "true"
    return "false"

@app.route("/change_password", methods=["POST"])
def change_account_password():
    if request.method == 'POST':
        old_password = request.form["old"]
        new_password = request.form["new"]
        email = request.form["email"]
        level = password_level(new_password)

        con = sqlite3.connect(f"db/passwords.db")

        cur = con.cursor()
        check_data = [i[0] for i in cur.execute(
            'SELECT hashed_password from passwords where email= "{}"'.format(
                email)).fetchall()][0]
        con.commit()
        con.close()
        if not check_password_hash(check_data, old_password):
            return "Неверный текущий пароль"
        if not level[0]:
            return level[1]
        con = sqlite3.connect(f"db/passwords.db")

        cur = con.cursor()

        cur = con.cursor()
        cur.execute("""UPDATE passwords
        SET hashed_password = '{}'
        WHERE email= '{}'""".format(generate_password_hash(new_password), email))
        con.commit()
        data = str(datetime.now().strftime("%d.%m.%Y %H:%M"))
        text = ["Здравствуйте!", f'''Уведомляем Вас о том, что {data.split()[0]} в {data.split()[1]} в аккаунте {email} сервиса "Помощник учителя" была произведена смена пароля.''', f"Новый пароль: {new_password}", "\nС уважением, разработчики."]

        stuff_mail(email, "Изменение пароля", '\n'.join(text))

        with open(f'db/accounts/{email}/info.json', "r",
                  encoding="utf-8") as f:
            a = json.load(f)
        a[-1] = str(datetime.now().strftime("%d.%m.%Y"))
        with open(f'db/accounts/{email}' + "/info.json", "w",
                  encoding="utf-8") as f:
            json.dump(a, f)
        return "ok"
    return "wrong_request"

@app.route("/exist_or_not/<email>", methods=["GET"])
def getinfo(email):
    result = {}
    con = sqlite3.connect(f"db/passwords.db")
    cur = con.cursor()
    check_data = [i[0] for i in cur.execute(
        'SELECT hashed_password from passwords where email= "{}"'.format(
            email)).fetchall()]

    con.commit()
    con.close()
    result["exist"] = bool(len(check_data))
    if bool(len(check_data)):
        result["email"] = email
        result["hashed-password"] = check_data[0]
    return jsonify(result)


@app.route('/account/<email>')
def acc(email):
    return render_template('account.html', title='Аккаунт', nick=email)

@app.route("/account_info/<email>", methods=["GET"])
def get_account_info(email):
    with open(f"db/accounts/{email}/info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/delete_datas/<email>", methods=["POST", "GET"])
def delete_links_or_notes(email):
    if request.method == 'POST':
        deletepart = [i.split("+-+") for i in
                      request.form["deletepart"].split('\n')]
        del_type = request.form["del_type"]
        with open(f"db/accounts/{email}/{del_type}.json", "r",
                  encoding="utf-8") as f:
            a = json.load(f)

        ok = [i for i in a if i not in deletepart]
        with open(f"db/accounts/{email}/{del_type}.json", "w",
                  encoding="utf-8") as f:
            json.dump(ok, f)
    return "deleted"


def sort_by_date_dates(object: list, k=1):
    objects = object.copy()
    try:
        objects = [(datetime.strptime(str(i[k]).lower(), "%d.%m.%Y %H:%M"), i)
                   for i in
                   object]
        objects.sort(key=lambda x: x[0])
        objects = [i[1] for i in objects]
        return objects

    except Exception as e:
        print(e.args)
        return objects


def window_search_data(email, del_type):
    with open(f"db/accounts/{email}/{del_type}.json", "r",
              encoding="utf-8") as f:
        a = json.load(f)
    result = {}
    result["Дате и времени"] = sort_by_date_dates(a)
    result["Названию"] = sorted(a, key=lambda x: x[0])
    result["look_data"] = [''.join([str(i) for i in j]).lower() for j in a]
    return result


def mess():
    global times, REMINDINGS_USERS, SEND_OR_NOT
    date = str(datetime.now().strftime("%d.%m.%Y %H:%M"))
    if date in times:
        for user in times[date]:
            stuff_mail(user[0], user[1], user[2])
            SEND_OR_NOT[user[0]] = False
            ok_mas = []
            for remind in REMINDINGS_USERS[user[0]]:
                if remind[0] != date or remind[1] != user[1] or remind[2] != \
                        user[2]:
                    ok_mas.append(remind)
            REMINDINGS_USERS[user[0]] = ok_mas.copy()
        del times[date]


def thr():
    while True:
        schedule.run_pending()
        time.sleep(1)


schedule.every(1).seconds.do(mess)
threading.Thread(target=thr).start()
if __name__ == "__main__":
    main()

    # exporting("nicolaynemov@mail.ru", "10Д", "10Д", True)
    # print(delete_class("nicolaynemov@mail.ru", "Shwabra262", "10А"))
    # pprint(workwindow("nicolaynemov@mail.ru"))

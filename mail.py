import mimetypes
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def stuff_mail(email, theme,
               text):  # отправка паролей для входа и проверочных кодов,
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


def send_mail(theme: str, text: str, files=[], emails=[]):
    text = (text.strip('\n')).strip()
    if not text.strip() and not theme.strip() and not files:
        return "here"
    for email in emails:
        message = MIMEMultipart()
        message["Subject"] = str(theme)
        message["From"] = 'nicolaynemov007@yandex.ru'
        for filepath in files:
            ctype, encoding = mimetypes.guess_type(
                filepath)  # Определяем тип файла на основе его расширения
            if ctype is None or encoding is not None:  # Если тип файла не определяется
                ctype = 'application/octet-stream'  # Будем использовать общий тип
            maintype, subtype = ctype.split('/', 1)  # Получаем тип и подтип
            with open(filepath, 'rb') as fp:
                file = MIMEBase(maintype,
                                subtype)  # Используем общий MIME-тип
                file.set_payload(
                    fp.read())  # Добавляем содержимое общего типа (полезную нагрузку)
            encoders.encode_base64(
                file)  # Содержимое должно кодироваться как Base64
            file.add_header('Content-Disposition', 'attachment',
                            filename=os.path.basename(
                                filepath))  # Добавляем заголовки
            message.attach(file)
        message.attach(MIMEText(text, 'plain'))
        try:
            if files:
                server = smtplib.SMTP_SSL("smtp.yandex.ru", 465)
                server.login(message["From"], "Shwabra26")
                server.sendmail(message["From"], email, message.as_string())
                return True
            else:

                a = (stuff_mail(email=email, theme=theme, text=text))
        except Exception as e:
            return e.args
    return True

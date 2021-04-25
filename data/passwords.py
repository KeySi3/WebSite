import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class Password(SqlAlchemyBase, UserMixin):
    __tablename__ = 'passwords'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)

    email = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=False, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=False, nullable=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
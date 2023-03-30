from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    login = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    power_supply = db.Column(db.Integer)
    status = db.Column(db.Boolean)
    pay_stat = db.Column(db.Boolean)
    power = db.relationship('Power', backref='user')
    temp = db.relationship('Temperature', backref='user')

    def __repr__(self):
        return f'<User {self.ID} {self.login}>'


class Power(db.Model):
    __tablename__ = 'power'
    time = db.Column(db.Integer, default=datetime.utcnow, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.ID'), primary_key=True)
    value = db.Column(db.Integer)

    def __repr__(self):
        return f'<Power {self.time} {self.value}>'


class Temperature(db.Model):
    __tablename__ = 'temperature'
    time = db.Column(db.Integer, default=datetime.utcnow, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.ID'), primary_key=True)
    value = db.Column(db.Integer)

    def __repr__(self):
        return f'<Temperature {self.time} {self.value}>'


with app.app_context():
    db.create_all()

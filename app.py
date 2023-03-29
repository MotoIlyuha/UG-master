from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import io
import base64
import matplotlib.pyplot as plt
from create_db import User, Power, Temperature


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login_customer = request.form['login']
        password = request.form['password']

        user = db.session.query(User).filter_by(login=login_customer).all()
        if len(user) != 0:
            user = user[0]
            if password == user.password:
                return redirect(f'/customer/{login_customer}/{password}')
            else:
                return redirect('/error')
        else:
            return redirect('/error')
    else:
        return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        login_customer = request.form['login']
        password = request.form['password']

        user = User(login=login_customer, password=password)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(f'/login')
        except:
            return redirect('/error')
    else:
        return render_template('register.html')


@app.route('/customer/<login>/<password>', methods=['POST', 'GET'])
def customer(login, password):
    user = db.session.query(User).filter_by(login=login).all()
    if len(user) != 0:
        user = user[0]
        if password == user.password:
            if request.method == 'POST':
                login_ = request.form['login']
                password_ = request.form['password']
            else:
                if login == "Admin":
                    return render_template('admin.html')
                elif login == "Operator":
                    return render_template('operator.html')
                else:
                    power_data, temp_data = get_info_by_period(user, None, None)
                    power = sum([i.value for i in power_data])
                    temp = sum([i.value for i in temp_data])
                    price = 5
                    cost = power*price
                    plt.plot(range(len(power_data)), [i.value for i in power_data], '-o')
                    img_1 = io.BytesIO()
                    plt.savefig(img_1, format='png')
                    plot_url_1 = base64.b64encode(img_1.getvalue()).decode()
                    plt.plot(range(len(temp_data)), [i.value for i in temp_data], '-o')
                    img_2 = io.BytesIO()
                    plt.savefig(img_2, format='png')
                    plot_url_2 = base64.b64encode(img_2.getvalue()).decode()
                    return render_template('customer.html', power=power, cost=cost, plot_url_1=plot_url_1, plot_url_2=plot_url_2)
        else:
            return redirect('/error')
    else:
        return redirect('/error')


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    return render_template('admin.html')


@app.route('/op', methods=['POST', 'GET'])
def op():
    return render_template('operator.html')


@app.route('/error', methods=['POST', 'GET'])
def error():
    return render_template('error.html')


def get_info_by_period(user, start=None, end=None):
    if start is None and end is None:
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID).all()
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID).all()
    else:
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID).filter(start <= Power.time <= end).all()
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID)\
            .filter(start <= Temperature.time <= end).all()
    return power_data, temp_data


def get_status(user):
    return user.status


def add_power_info(time, user, value):
    u = User.query.get(user)
    p = Power(time=time, user=u, value=value)
    db.session.add(p)
    db.session.commit()


def add_temp_info(time, user, value):
    u = User.query.get(user)
    p = Temperature(time=time, user=u, value=value)
    db.session.add(p)
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from create_db import User, Power, Temperature
from time import strftime, gmtime
import datetime
import pdfkit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
users_data = list()


def users_data_init(start=None, end=None):
    global users_data
    users_data = list()
    price = 5
    users = db.session.query(User).filter_by(role=0).all()
    ids = [user.ID for user in users]
    power_and_temp = [get_info_by_period(user, start, end) for user in users]
    power_sum = [sum([p.value for p in user[0]]) for user in power_and_temp]
    power_plt_data = [[p.value for p in user[0]] for user in power_and_temp]
    temp_plt_data = [[t.value for t in user[1]] for user in power_and_temp]
    label_plt = [[t.time for t in user[2]] for user in power_and_temp]
    costs = [user * price for user in power_sum]
    powers_supply = [user.power_supply for user in users]
    state = [user.status for user in users]
    logins = [user.login for user in users]
    pay_stats = [user.pay_stat for user in users]
    minutes_str = [[strftime('%M:%S', gmtime(t // 1000)) for t in user] for user in label_plt]
    for i in range(len(users)):
        users_data.append({"id": ids[i], "power_sum": power_sum[i], "power_plt_data": power_plt_data[i],
                           "temp_plt_data": temp_plt_data[i], "cost": costs[i], "powers_supply": powers_supply[i],
                           "login": logins[i], "state": state[i], "pay_stat": pay_stats[i], "label_plt": label_plt[i],
                           "minutes": minutes_str[i]})


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
    cur_user = db.session.query(User).filter_by(login=login).all()[0]
    if password == cur_user.password:
        users_data_init()
        if login == "Admin":
            return render_template('admin.html', users_data=users_data, index=0)
        elif login == "Operator":
            return render_template('operator.html', users_data=users_data)
        else:
            user_data = users_data[cur_user.ID - 1]
            return render_template('customer.html', user_data=user_data)
    else:
        return redirect('/error')


@app.route('/customer/<login>/date', methods=['POST', 'GET'])
def change_customer_period(login):
    users_data_init(request.form['start'], request.form['end'])
    cur_user = db.session.query(User).filter_by(login=login).all()[0]
    user_data = users_data[cur_user.ID - 1]
    return render_template('customer.html', user_data=user_data)


@app.route('/admin/<login>/date', methods=['POST', 'GET'])
def change_admin_period(login):
    cur_user = db.session.query(User).filter_by(login=login).all()[0]
    users_data_init(request.form['start'], request.form['end'])
    return render_template('admin.html', users_data=users_data, index=cur_user.ID-1)


@app.route('/admin/<login>/<check>/', methods=['POST', 'GET'])
def change_customer(login, check):
    cur_user = db.session.query(User).filter_by(login=login).all()[0]
    if check != '0':
        user = db.session.query(User).filter_by(ID=check).all()[0]
        user.status = not user.status
        db.session.commit()
    users_data_init()
    return render_template('admin.html', users_data=users_data, index=cur_user.ID-1)


@app.route('/error', methods=['POST', 'GET'])
def error():
    return render_template('error.html')


def get_info_by_period(user, start=None, end=None):
    if start is None and end is None:
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID).all()
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID).all()
        time_data = db.session.query(Power.time).filter_by(user_id=user.ID).all()
        return power_data, temp_data, time_data
    else:
        # 7 часов пропадает, потому что часовой пояс +7 часов
        start = (int(datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M").timestamp()) + 7 * 60 * 60) * 1000
        end = (int(datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M").timestamp()) + 7 * 60 * 60) * 1000
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID)\
            .filter(start <= Power.time, Power.time <= end).all()
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID) \
            .filter(start <= Temperature.time, Temperature.time <= end).all()
        time_data = db.session.query(Power.time).filter_by(user_id=user.ID)\
            .filter(start <= Power.time, Power.time <= end).all()
        return power_data, temp_data, time_data


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


def generate_pdf(date):
    pdf_template = render_template('pdf_temp.html', users_data=users_data, date=date)
    pdfkit.from_string(pdf_template, 'Отчёт.pdf')


if __name__ == '__main__':
    app.run(debug=True)

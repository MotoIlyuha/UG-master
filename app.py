from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from create_db import User, Power, Temperature

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
users_data = list()


def users_data_init():
    price = 5
    users = db.session.query(User).filter_by(role=0).all()
    power_and_temp = [get_info_by_period(user, None, None) for user in users]
    power_sum = [sum([p.value for p in user[0]]) for user in power_and_temp]
    power_plt_data = [[p.value for p in user[0]] for user in power_and_temp]
    temp_plt_data = [[t.value for t in user[1]] for user in power_and_temp]
    label_plt = [[t.time for t in user[2]] for user in power_and_temp]
    costs = [user[0] * price for user in power_and_temp]
    powers_supply = [user.power_supply for user in users]
    state = [user.status for user in users]
    logins = [user.login for user in users]
    pay_stats = [user.pay_stat for user in users]
    for i in range(len(users)):
        users_data.append({"power_sum": power_sum[i], "power_plt_data": power_plt_data[i],
                           "temp_plt_data": temp_plt_data[i], "cost": costs[i], "powers_supply": powers_supply[i],
                           "login": logins[i], "state": state[i], "pay_stat": pay_stats[i], "label_plt": label_plt})


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
    if password == cur_user.password and request.method != 'POST':
        if login == "Admin":
            users_data_init()
            return render_template('admin.html', users_data=users_data)
        elif login == "Operator":
            return render_template('operator.html')
        else:
            pass
            # ptt = get_info_by_period(cur_user, None, None)
            # power = sum([i.value for i in power_data])
            # price = 5
            # cost = power * price
            # plot_url_1 = [i.value for i in power_data]
            # plot_url_2 = [i.value for i in temp_data]
            # return render_template('customer.html', power=power, cost=cost, label=list(range(0, len(power_data))),
            #                        power_data=plot_url_1, temp_data=plot_url_2)
    else:
        return redirect('/error')


@app.route('/error', methods=['POST', 'GET'])
def error():
    return render_template('error.html')


def get_info_by_period(user, start=None, end=None):
    if start is None and end is None:
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID).all()
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID).all()
        time = db.session.query(Power.time).filter_by(user_id=user.ID).all()
        time_period = (time[0], time[-1])
        return power_data, temp_data, time_period
    else:
        power_data = db.session.query(Power.value).filter_by(user_id=user.ID).filter(start <= Power.time <= end).all()
        temp_data = db.session.query(Temperature.value).filter_by(user_id=user.ID) \
            .filter(start <= Temperature.time <= end).all()
        return power_data, temp_data, (start, end)


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

import random

from paho.mqtt import client as mqtt_client

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


broker = 'mqtt.by'
port = 1883

prefix = 'user/LaghZen/'
Energy_Source = 'Energy_Source'

client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'LaghZen'
password = 'Souz____'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, topic, msg):
    result = client.publish(topic, str(msg))

    status = result[0]
    if status == 0:
        print(f"Send messages: '{msg}' to topic '{topic}'")
    else:
        print(f"Failed to send message to topic {topic}")


def subscribe(client, topic):
    def on_message(client, userdata, msg):
        login = msg.payload.decode().split('~')[0]
        value = msg.payload.decode().split('~')[1]
        user = History(login=login, value=value)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            pass
        print(f"Received '{msg.payload.decode()}' from '{msg.topic}' topic")

    client.subscribe(topic)
    client.on_message = on_message


class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    value = db.Column(db.Integer)

    def __repr__(self):
        return '<History %r>' % self.id


if __name__ == "__main__":
    with app.app_context():
        def on_message(client, userdata, msg):
            login = msg.payload.decode().split('~')[0]
            value = msg.payload.decode().split('~')[1]
            user = History(login=login, value=value)
            try:
                db.session.add(user)
                db.session.commit()
            except:
                pass


    client = connect_mqtt()
    subscribe(client, prefix+Energy_Source)
    publish(client, prefix+Energy_Source, 123)

    client.loop_forever()

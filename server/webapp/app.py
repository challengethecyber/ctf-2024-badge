from flask import Flask, render_template, g, request
import sqlite3
from datetime import datetime
import json
from paho.mqtt import client as mqtt_client

app = Flask(__name__)

BROKER = "192.168.76.2" # 192.168.76.2

class Score:
    def __init__(self, data):
        self.teamnum = data[0]
        self.teamname = data[1]
        self.highscore = data[2]
        self.lastupdate = data[3]
        self.visibility = data[4]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('data.db')
    return db


@app.route('/<int:view>')
def dashboard(view):
    cur = get_db().execute("SELECT * FROM scores WHERE visibility ORDER BY highscore DESC, lastupdate DESC;")
    data = cur.fetchall()
    cur.close()

    allscores = [Score(d) for d in data]
    maxviews = ((len(allscores)-1) // 10) + 1
    nextview = (view % maxviews) + 1

    scores = allscores[10*(view-1):][:10]
    scores_left = scores[:5]
    scores_right = scores[5:] if len(scores) >=5 else []

    return render_template('scores.html', scores_left=scores_left, scores_right=scores_right, curview=view, nextview=nextview, maxviews=maxviews)

## to check: thread safety?

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def mqtt_connect():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")

            client.on_message = mqtt_message
            client.subscribe("score/+")
        else:
            print("Failed to connect, return code %d\n", rc)

    import random
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, f'adm-{random.randint(0, 1000)}')
    if "192." in BROKER:
        client.username_pw_set("adm", "Woooptiedooptiedoooooo")
    client.on_connect = on_connect
    client.connect(BROKER, 1883)
    
    return client

def mqtt_message(client, userdata, msg):
    if msg.topic.startswith("score/"):
        _, team_num = msg.topic.split("/")
        
        score = None
        try:
            jl = json.loads(msg.payload)
            if "score" in jl:
                score = min(9000, max(0, int(jl["score"])))
        except:
            pass
        
        if score:
            with app.app_context():
                db = get_db()
                cur = db.execute("UPDATE scores SET highscore = MIN(9000, MAX(highscore, ?)), lastupdate=CURRENT_TIMESTAMP WHERE teamnum = ?", (score,team_num,))
                db.commit()
                cur.close()


if __name__ == "__main__":
    mqtt_client = mqtt_connect()
    mqtt_client.loop_start()
    app.run(debug=False, host='127.0.0.1', port=5002)

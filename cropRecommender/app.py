from flask import Flask, render_template,url_for, request, flash
import sqlite3
from flask_bootstrap import Bootstrap
import pickle
import pandas as pd



pickle_in = open('crop_recommender.pkl', 'rb')
model = pickle.load(pickle_in)

app = Flask(__name__, static_url_path='/static')
Bootstrap(app)



@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/addrec', methods=['POST', 'GET'])
def addrec():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            farm_name = request.form['farm_name']
            username = request.form['username']
            password = request.form['password']
            with sqlite3.connect("user_data.db") as con:
                cur = con.cursor()
                cur.execute("INSERT into users (first_name, last_name, farm_name, username, password)VALUES(?,?,?,?,?)",
                            (first_name, last_name, farm_name, username, password))
                con.commit()
                msg = "Registration Complete."
        except:
            con.rollback()
            msg = "Unable to complete registration."
            return render_template("home.html", msg=msg)
        finally:
            return render_template("login.html", msg=msg)




@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/getinfo', methods=['POST','GET'])
def getinfo():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            with sqlite3.connect("user_data.db") as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password))
                if cur.fetchone() is not None:
                    return render_template("cropRecommender.html")
                else:
                    msg = "Login Failed."
                    return render_template("login.html", msg=msg)
        except:
            error = "Try again."
            return render_template("login.html", error=error)




@app.route('/cropRecommender')
def cropRecommender():
    return render_template('cropRecommender.html')

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        pH = request.form['pH']
        N = request.form['N']
        P = request.form['P']
        K = request.form['K']
        OC = request.form['OC']
        Particles = request.form['Particles']
        Water_holding_content = request.form['Water_holding_content']
        Soil_type = request.form['Soil_type']

        input_variables = pd.DataFrame([[pH, N, P, K, OC, Particles, Water_holding_content, Soil_type]],
                                       columns=[pH, N, P, K, OC, Particles, Water_holding_content, Soil_type],
                                       dtype=float)
        prediction = model.predict(input_variables)[0]

        with sqlite3.connect("soil_data.db") as con:
            cur = con.cursor()
            cur.execute("INSERT into analysis (pH, N, P, K, OC, Particles, Water_holding_content, "
                        "Soil_type, prediction)VALUES(?,?,?,?,?,?,?,?,?)",
                        (pH, N, P, K, OC, Particles, Water_holding_content, Soil_type, prediction))
            con.commit()

    return render_template("result.html", prediction=prediction)

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/admin')
def adminlogin():
    return render_template('admin.html')


@app.route('/admin', methods=['POST'])
def admin():
    if request.form['password'] == 'admin1234' and request.form['username'] == 'admin':
        return render_template('dashboard.html')
    else:
        flash('wrong password!')

@app.route('/dashboard')
def dashboard():
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    """conn = sqlite3.connect("soil_data.db")
    curr = conn.cursor()
    curr.execute("SELECT * FROM analysis")
    data = curr.fetchall()"""
    return render_template("dashboard.html", rows=rows, data=data)


@app.route('/logout')
def logout():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)

# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 10:08:53 2019

@author: demerss1
"""
import sqlite3
import os

import datetime as dt

from functools import wraps
from typing import List
from passlib.hash import sha256_crypt
from flask import Flask, render_template, redirect, request, url_for, \
                  make_response, session

# adjust path to run from development or production env
path = os.getcwd()
path = path[path.rindex("\\") + 1:]
if path == "Web Application":
    from myApp.database_setup import qquery
    db = "myApp/water.db"
else:
    from database_setup import qquery
    db = "water.db"


app = Flask(__name__)
app.secret_key = 'water is life and we take it for granted'


def get_data(Id: int, modules: List[str],
             dur: str = "1M") -> List[List[object]]:
    """
    Gets the tester data and returns valus as a List[List[object]]
    object is default becasue it can vary depending on columns
    Also can vary on the size depending on the installed modules

    Id is the tester Id
    modules is the list of installed modules from the u_info
    dur is the duration set by the user, default is 1 month
    """
    modules = ",".join(modules)
    if dur == "all":
        data = qquery(f"SELECT {modules} FROM tester_data WHERE ID = {Id}")
    else:  # get the duration from database
        if dur == "1M":
            qstring = "-1 month"
        elif dur == "3M":
            qstring = "-3 month"
        elif dur == "6M":
            qstring = "-6 month"
        elif dur == "12M":
            qstring = "-1 year"
        data = qquery(f"""
                      SELECT {modules}
                      FROM tester_data
                      WHERE ID = {Id} AND
                      date <= DATETIME('now') AND
                      date >= DATETIME('now', '{qstring}')
                      """)
    data.Coliform = data["Coliform"].apply(lambda x: True if x == 1 else False)
    return data.values.tolist()


# setup decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user')
        if user_id is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# main page
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        user_id = request.cookies.get('user')
        selected_id = int(request.form.get('testerId'))
        duration = request.form.get("duration")
        query = f"SELECT * FROM user_info WHERE userName = '{user_id}'"
        u_info = qquery(query)
        tester_ids = u_info.ID.tolist()
        u_info = u_info[u_info.ID == selected_id]  # get data for only that ID
        frequency = u_info.frequency.values[0]
        drop_cols = ['ID', 'userName', 'password', 'frequency']
        u_info = u_info.drop(drop_cols, axis=1)

        # get installed modules on device
        modules = [c for c in u_info.columns if u_info[c].values[0] == 1]
        data = get_data(selected_id, modules, duration)
        return render_template("index.html", user=user_id, frequency=frequency,
                               ids=tester_ids, selected_id=selected_id,
                               modules=modules, tData=data,
                               selected_dur=duration)
    else:
        user_id = request.cookies.get('user')
        query = f"SELECT * FROM user_info WHERE userName = '{user_id}'"
        u_info = qquery(query)
        tester_ids = u_info.ID.tolist()
        selected_id = tester_ids[0]  # default to first id
        u_info = u_info[u_info.ID == selected_id]
        frequency = u_info.frequency.values[0]
        drop_cols = ['ID', 'userName', 'password', 'frequency']
        u_info = u_info.drop(drop_cols, axis=1)

        # get installed modules on device
        modules = [c for c in u_info.columns if u_info[c].values[0] == 1]
        data = get_data(selected_id, modules)
        return render_template("index.html", user=user_id, frequency=frequency,
                               ids=tester_ids, selected_id=selected_id,
                               modules=modules, tData=data)


# register a new tester
@app.route('/register-new-tester', methods=['GET', 'POST'])
@login_required
def register_new_tester():
    if request.method == "POST":
        t_info = qquery("SELECT * FROM tester_info")
        u_info = qquery("SELECT * FROM user_info")
        tester_ids = list(t_info.ID)
        used_ids = sorted(u_info.ID)

        # get user input
        try:
            tester_id = int(request.form.get("testerId").strip())
            confirm_id = int(request.form.get("confirmId").strip())
        except ValueError:
            msg = "Invalid tester number"
            return render_template("register_tester.html", message=msg)

        # check if tester number exists
        if tester_id not in tester_ids:
            msg = "Incorrect Tester number, does not exists"
            return render_template("register_tester.html", message=msg)

        # check if tester numbers match
        if tester_id != confirm_id:
            msg = "Tester numbers do not match"
            return render_template("register_tester.html", message=msg)

        # check if tester number was used
        if tester_id in used_ids:
            msg = "Tester number has been registered already"
            return render_template("register_tester.html", message=msg)

        # successfully registered
        user_id = request.cookies.get('user')
        row = u_info[u_info.userName == user_id].iloc[0]
        password = row.password
        row = t_info[t_info.ID == tester_id].iloc[0]
        values = f"{tester_id}, '{user_id}', '{password}', 30, {row.pH}, "
        values += f"{row.TDS}, {row.Coliform}"
        query = f"INSERT INTO user_info VALUES ({values});"
        with sqlite3.connect(db) as con:
            con.cursor().execute(query)
            con.commit()
        return redirect(url_for('index'))

    return render_template("register_tester.html", message="none")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get current database of users and passwords
        u_info = qquery("SELECT * FROM user_info")
        usernames = list(u_info.userName)
        passwords = list(u_info.password)

        # get user input
        user_id = request.form.get("username").strip()
        pswd = request.form.get("pswd").strip()

        # check to see if user name exists
        if user_id not in usernames:
            msg = "Incorrect username"
            return render_template("login.html", message=msg)

        # check to see if password name
        for p in passwords:
            if not sha256_crypt.verify(pswd, p):
                msg = "Incorrect password"
                return render_template("login.html", message=msg)

        # get row of inputed username
        row = u_info[u_info.userName == user_id].iloc[0]

        # The username and password do not match
        if not sha256_crypt.verify(pswd, row.password):
            msg = "Incorrect username or password"
            return render_template("login.html", message=msg)

        # username and password match
        # set session and cookie
        session['log'] = True
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('user', user_id)
        return resp

    return render_template("login.html", message="none")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        t_info = qquery("SELECT * FROM tester_info")
        u_info = qquery("SELECT * FROM user_info")
        tester_ids = list(t_info.ID)
        used_ids = sorted(u_info.ID)

        # get user inputs
        try:
            tester_id = int(request.form.get("testerId").strip())
        except ValueError:
            msg = "Invalid tester number"
            return render_template("register.html", message=msg)

        user_id = request.form.get("username").strip()
        password = request.form.get("pswd").strip()
        confirm = request.form.get("confirm").strip()

        # cheack to see if password requirments are met
        check_digit = any(char.isdigit() for char in password)
        check_upper = any(char.isupper() for char in password)
        check_lower = any(char.islower() for char in password)
        check_len = len(password) > 7
        if not check_digit or not check_upper or \
           not check_lower or not check_len:
            msg = "password requirment is not met"
            return render_template("register.html", message=msg)

        # check for user input errors
        if password != confirm:
            msg = "passwords do not match"
            return render_template("register.html", message=msg)

        if tester_id not in tester_ids:
            msg = "Incorrect Tester number, does not exists"
            return render_template("register.html", message=msg)

        if tester_id in used_ids:
            msg = "Tester number has been registered already"
            return render_template("register.html", message=msg)

        # user name and password combo check
        if user_id in list(u_info.userName):
            row = u_info[u_info.userName == user_id].iloc[0]
            if sha256_crypt.verify(password, row.password):
                msg = "Username and password combo already exists"
                return render_template("register.html", message=msg)

        # good register so set data
        secure_pswd = sha256_crypt.hash(password)
        row = t_info[t_info.ID == tester_id].iloc[0]
        values = f"{tester_id}, '{user_id}', '{secure_pswd}', 30, {row.pH}, "
        values += f"{row.TDS}, {row.Coliform}"
        query = f"INSERT INTO user_info VALUES ({values});"
        with sqlite3.connect(db) as con:
            con.cursor().execute(query)
            con.commit()
        return redirect(url_for('login'))
    else:
        return render_template("register.html", message="none")


# resource endpoints
@app.route('/update_freq', methods=['POST'])
def update_freq():
    req = request.get_json()
    tester_id = int(req["id"])
    frequency = int(req["frequency"])
    query = f"""UPDATE user_info
                SET frequency = {frequency}
                WHERE ID = {tester_id}"""
    with sqlite3.connect(db) as con:
        con.cursor().execute(query)
        con.commit()
    return "Submitted"


@app.route('/get_freq', methods=['POST'])
# TODO return the frequncy for that testerID for Brody to set interval
# TODO check if it is better with POST or GET
@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    print(data)

    # check for errors
    try:
        ID = int(data["ID"])
        pH = float(data['pH'])
        TDS = float(data['TDS'])
        coliform = bool(data['coliform'])
    except ValueError as e:
        print("Invalid data Transfer", e, "\n")
        return f'Invalid I got data'
    date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    values = f"{ID}, {date}, '{pH}', '{TDS}', {coliform}"
    query = f"INSERT INTO tester_data VALUES ({values});"
    with sqlite3.connect(db) as con:
        con.cursor().execute(query)
        con.commit()
    return "success"


@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('user', '', expires=0)  # clear cookie
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)

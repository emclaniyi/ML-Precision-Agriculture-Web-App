"""Canonical Flask application for the Smart Farm recommender."""

from pathlib import Path
import os
import pickle
import sqlite3

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv

from db import SOIL_DATABASE, USER_DATABASE, get_connection, init_db


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
MODEL_PATH = BASE_DIR / "models" / "crop_recommender.pkl"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
FEATURE_COLUMNS = [
    "pH",
    "N",
    "P",
    "K",
    "OC",
    "Particles",
    "Water_holding_content",
    "Soil_type",
]


app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "development-only-change-me"
)
Bootstrap(app)
init_db()


def load_model():
    """Load the model only when a prediction is requested."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
    with MODEL_PATH.open("rb") as model_file:
        return pickle.load(model_file)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/addrec", methods=["POST"])
def addrec():
    fields = ["first_name", "last_name", "farm_name", "username", "password"]
    values = [request.form.get(field, "").strip() for field in fields]

    if not all(values):
        return render_template(
            "register.html", msg="Please complete every registration field."
        ), 400

    try:
        with get_connection(USER_DATABASE) as connection:
            connection.execute(
                """
                INSERT INTO users
                    (first_name, last_name, farm_name, username, password)
                VALUES (?, ?, ?, ?, ?)
                """,
                values,
            )
    except sqlite3.Error:
        return render_template(
            "register.html", msg="Unable to complete registration."
        ), 400

    return render_template("login.html", msg="Registration Complete.")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/getinfo", methods=["POST"])
def getinfo():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    with get_connection(USER_DATABASE) as connection:
        user = connection.execute(
            "SELECT 1 FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()

    if user is None:
        return render_template("login.html", msg="Login Failed."), 401

    return redirect(url_for("crop_recommender"))


@app.route("/cropRecommender")
def crop_recommender():
    return render_template("cropRecommender.html")


@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    if request.method == "GET":
        return redirect(url_for("crop_recommender"))

    try:
        values = [float(request.form[column]) for column in FEATURE_COLUMNS]
    except (KeyError, TypeError, ValueError):
        return render_template(
            "cropRecommender.html",
            msg="Please enter valid numeric values for every soil field.",
        ), 400

    input_variables = pd.DataFrame([values], columns=FEATURE_COLUMNS)

    try:
        prediction = int(load_model().predict(input_variables)[0])
    except Exception:
        app.logger.exception("Model prediction failed")
        return render_template(
            "cropRecommender.html",
            msg="The recommendation model is not ready. Please contact the administrator.",
        ), 503

    with get_connection(SOIL_DATABASE) as connection:
        connection.execute(
            """
            INSERT INTO analysis
                (pH, N, P, K, OC, Particles, Water_holding_content, Soil_type, prediction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*values, prediction),
        )

    return render_template("result.html", prediction=prediction)


@app.route("/result")
def result():
    return redirect(url_for("crop_recommender"))


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/adminlogin", methods=["POST"])
def adminlogin():
    expected_username = os.environ.get("ADMIN_USERNAME", "admin")
    expected_password = os.environ.get("ADMIN_PASSWORD", "admin1234")

    if (
        request.form.get("username") == expected_username
        and request.form.get("password") == expected_password
    ):
        return redirect(url_for("dashboard"))

    flash("Wrong username or password.")
    return redirect(url_for("admin"))


@app.route("/dashboard")
def dashboard():
    with get_connection(USER_DATABASE) as connection:
        rows = connection.execute("SELECT * FROM users").fetchall()

    with get_connection(SOIL_DATABASE) as connection:
        data = connection.execute("SELECT * FROM analysis").fetchall()

    return render_template("dashboard.html", rows=rows, data=data)


@app.route("/logout")
def logout():
    return redirect(url_for("home"))

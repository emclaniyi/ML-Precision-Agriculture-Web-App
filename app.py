"""Smart Farm Flask application."""

from functools import wraps
from pathlib import Path
import hmac
import math
import os
import secrets
import sqlite3

import joblib
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import SOIL_DATABASE, USER_DATABASE, get_connection, init_db


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
MODEL_PATH = BASE_DIR / "models" / "crop_recommender.joblib"
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
NUMERIC_COLUMNS = FEATURE_COLUMNS[:-1]
SOIL_TYPES = {"clay", "Sandy", "loamy"}


app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "development-only-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("APP_ENV") == "production",
)
init_db()


def csrf_token() -> str:
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_template_context():
    return {
        "csrf_token": csrf_token,
        "current_username": session.get("username"),
        "is_admin": session.get("is_admin", False),
    }


def require_csrf() -> None:
    supplied = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        abort(400, description="Invalid form token.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin"))
        return view(*args, **kwargs)

    return wrapped


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def is_password_hash(value: str) -> bool:
    return value.startswith(("scrypt:", "pbkdf2:"))


def validate_soil_input(form: dict) -> dict:
    values = {}
    for column in NUMERIC_COLUMNS:
        value = float(form[column])
        if not math.isfinite(value):
            raise ValueError(f"{column} must be finite")
        values[column] = value

    if not 0 <= values["pH"] <= 14:
        raise ValueError("pH must be between 0 and 14")
    if any(values[column] < 0 for column in NUMERIC_COLUMNS[1:]):
        raise ValueError("Soil measurements cannot be negative")

    soil_type = form["Soil_type"]
    if soil_type not in SOIL_TYPES:
        raise ValueError("Choose a valid soil type")
    values["Soil_type"] = soil_type
    return values


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/addrec", methods=["POST"])
def addrec():
    require_csrf()
    fields = ["first_name", "last_name", "farm_name", "username", "password", "confirm_password"]
    values = {field: request.form.get(field, "").strip() for field in fields}

    if not all(values.values()):
        return render_template("register.html", msg="Please complete every registration field."), 400
    if values["password"] != values["confirm_password"]:
        return render_template("register.html", msg="Passwords do not match."), 400
    if len(values["password"]) < 8:
        return render_template("register.html", msg="Password must be at least 8 characters."), 400

    try:
        with get_connection(USER_DATABASE) as connection:
            connection.execute(
                """
                INSERT INTO users (first_name, last_name, farm_name, username, password)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    values["first_name"],
                    values["last_name"],
                    values["farm_name"],
                    values["username"],
                    generate_password_hash(values["password"]),
                ),
            )
    except sqlite3.IntegrityError:
        return render_template("register.html", msg="That username is already in use."), 409

    return render_template("login.html", msg="Registration complete. You can now sign in.")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/getinfo", methods=["POST"])
def getinfo():
    require_csrf()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    with get_connection(USER_DATABASE) as connection:
        user = connection.execute(
            "SELECT username, password FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        valid = False
        if user:
            stored_password = user["password"]
            if is_password_hash(stored_password):
                valid = check_password_hash(stored_password, password)
            else:
                valid = hmac.compare_digest(stored_password, password)
                if valid:
                    connection.execute(
                        "UPDATE users SET password = ? WHERE username = ?",
                        (generate_password_hash(password), username),
                    )

    if not valid:
        return render_template("login.html", msg="Login failed. Check your details and try again."), 401

    session.clear()
    session["username"] = username
    csrf_token()
    return redirect(url_for("crop_recommender"))


@app.route("/cropRecommender")
@login_required
def crop_recommender():
    return render_template("cropRecommender.html")


@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    if request.method == "GET":
        return redirect(url_for("crop_recommender"))

    require_csrf()
    try:
        values = validate_soil_input(request.form)
    except (KeyError, TypeError, ValueError):
        return render_template("cropRecommender.html", msg="Please enter valid soil measurements."), 400

    input_variables = pd.DataFrame([values], columns=FEATURE_COLUMNS)
    try:
        prediction = str(load_model().predict(input_variables)[0])
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
                (pH, N, P, K, OC, Particles, Water_holding_content, Soil_type, prediction, username, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            tuple(values[column] for column in FEATURE_COLUMNS) + (prediction, session["username"]),
        )

    return render_template("result.html", prediction=prediction)


@app.route("/result")
@login_required
def result():
    return redirect(url_for("crop_recommender"))


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/adminlogin", methods=["POST"])
def adminlogin():
    require_csrf()
    expected_username = os.environ.get("ADMIN_USERNAME")
    expected_password = os.environ.get("ADMIN_PASSWORD")
    if not expected_username or not expected_password:
        flash("Admin access is not configured.")
        return redirect(url_for("admin"))

    if (
        hmac.compare_digest(request.form.get("username", ""), expected_username)
        and hmac.compare_digest(request.form.get("password", ""), expected_password)
    ):
        session.clear()
        session["is_admin"] = True
        csrf_token()
        return redirect(url_for("dashboard"))

    flash("Wrong username or password.")
    return redirect(url_for("admin"))


@app.route("/dashboard")
@admin_required
def dashboard():
    with get_connection(USER_DATABASE) as connection:
        rows = connection.execute(
            "SELECT first_name, last_name, farm_name, username FROM users ORDER BY last_name, first_name"
        ).fetchall()

    with get_connection(SOIL_DATABASE) as connection:
        data = connection.execute(
            """
            SELECT pH, N, P, K, OC, Particles, Water_holding_content,
                   Soil_type, prediction, username, created_at
            FROM analysis ORDER BY rowid DESC
            """
        ).fetchall()

    return render_template("dashboard.html", rows=rows, data=data)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

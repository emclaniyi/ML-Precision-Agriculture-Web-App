"""Small SQLite helpers used by the Flask application."""

from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
USER_DATABASE = INSTANCE_DIR / "user_data.db"
SOIL_DATABASE = INSTANCE_DIR / "soil_data.db"


def get_connection(database_path: Path) -> sqlite3.Connection:
    """Open a connection to one of the application databases."""
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the application tables when they do not already exist."""
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection(USER_DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                farm_name TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
            """
        )

    with get_connection(SOIL_DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis (
                pH TEXT NOT NULL,
                N TEXT NOT NULL,
                P TEXT NOT NULL,
                K TEXT NOT NULL,
                OC TEXT NOT NULL,
                Particles TEXT NOT NULL,
                Water_holding_content TEXT NOT NULL,
                Soil_type TEXT NOT NULL,
                prediction TEXT NOT NULL
            )
            """
        )

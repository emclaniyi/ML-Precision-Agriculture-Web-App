"""SQLite helpers and lightweight schema setup for Smart Farm."""

from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
USER_DATABASE = INSTANCE_DIR / "user_data.db"
SOIL_DATABASE = INSTANCE_DIR / "soil_data.db"


def get_connection(database_path: Path) -> sqlite3.Connection:
    """Open a row-addressable SQLite connection."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_column(connection: sqlite3.Connection, table: str, name: str, definition: str) -> None:
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    if name not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def init_db() -> None:
    """Create or upgrade local tables without deleting existing data."""
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
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)"
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
        _ensure_column(connection, "analysis", "username", "TEXT")
        _ensure_column(connection, "analysis", "created_at", "TEXT")

import sqlite3 as sql

"""con = sql.connect('user_data.db')
print("Database opened successfully")


con.execute("CREATE TABLE users (last_name TEXT, first_name TEXT,"
            " farm_name TEXT, username VARCHAR, password VARCHAR)")
print("Table created successfully")
con.close()


con = sql.connect('soil_data.db')
print("Database opened successfully")


con.execute("CREATE TABLE analysis (pH VARCHAR, N VARCHAR, P VARCHAR, K VARCHAR, OC VARCHAR,"
            "Particles VARCHAR, Water_holding_content VARCHAR, Soil_type VARCHAR, prediction VARCHAR)")
print("Table created successfully")
con.close()

con = sql.connect("user_data.db")
#con.row_factory = sql.Row
cur = con.cursor()
cur.execute("SELECT * FROM users")
rows = cur.fetchall()
print(rows)
for i in rows:
    print(i)"""

from flask_sqlalchemy import SQLAlchemy

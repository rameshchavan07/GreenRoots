import mysql.connector

dbuser = "root"         # or your MySQL username
dbpass = "$3rv3r1@R"
dbhost = "localhost"
dbport = "3306"
dbname = "agrihire"

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=dbhost,
            user=dbuser,
            password=dbpass,
            port=dbport,
            database=dbname
        )
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None

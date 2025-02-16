import mysql.connector
import psycopg2

def get_connection(username, host, password):
    try:
        conn = mysql.connector.connect(user=username, password=password, host=host)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_postgres_connection(username, host, password):
    try:
        conn = psycopg2.connect(user=username, password=password, host=host)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
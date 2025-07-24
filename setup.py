import json
import pymysql as MySQLdb

def create_config():
    db_user = input("Enter MySQL username: ").strip()
    db_password = input("Enter MySQL password: ").strip()
    db_name = input("Enter MySQL database name: ").strip()

    config = {
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_HOST": "localhost",
        "DB_PORT": 3306,
        "DB_NAME": db_name
    }

    with open('config.json', 'w') as f:
        json.dump(config, f)

    print("Configuration saved.")

    create_database_and_insert_data(db_user, db_password, db_name)

def create_database_and_insert_data(db_user, db_password, db_name):
    db = MySQLdb.connect(host="localhost", user=db_user, passwd=db_password)
    cursor = db.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    db.select_db(db_name)

    dump_file_path = 'backup.sql'
    execute_sql_dump(cursor, dump_file_path)

    db.commit()
    db.close()
    print(f"Database '{db_name}' created and initial data inserted.")

def execute_sql_dump(cursor, dump_file_path):
    with open(dump_file_path, 'r') as f:
        sql_statements = f.read()

    for statement in sql_statements.split(';'):
        try:
            if statement.strip():
                cursor.execute(statement)
        except Exception as e:
            print(f"Error executing SQL statement: {e}")

if __name__ == "__main__":
    create_config()

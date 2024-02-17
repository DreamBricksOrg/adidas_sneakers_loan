from flask_mysqldb import MySQL

mysql = MySQL()

def initialize_mysql(app):
    app.config['MYSQL_HOST'] = '54.233.111.126'
    app.config['MYSQL_USER'] = 'db'
    app.config['MYSQL_PASSWORD'] = '3177'
    app.config['MYSQL_DB'] = 'adidas'
    mysql.init_app(app)

    return mysql
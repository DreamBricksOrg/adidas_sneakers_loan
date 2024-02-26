from flask_mysqldb import MySQL

mysql = MySQL()

def initialize_mysql(app):
    app.config['MYSQL_HOST'] = 'supernova.sytes.net'
    app.config['MYSQL_USER'] = 'db'
    app.config['MYSQL_PASSWORD'] = 'UzoEuMDNrBupB5E6z8DfqKgMW'
    app.config['MYSQL_DB'] = 'adidas'
    mysql.init_app(app)

    return mysql

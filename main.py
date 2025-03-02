from flask import Flask, request, make_response 
from flask_mysqldb import MySQL
import bcrypt
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet

load_dotenv()

app = Flask(__name__)
token_gen = Fernet(os.getenv('SECRET_KEY').encode('utf-8'))

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER']= os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')


mysql = MySQL(app)

@app.route("/hello")
@app.route("/")
def home():
    token = request.headers.get('Authorization')
    if token:
        token_encoded = token.encode()
        userid_encoded = token_gen.decrypt(token_encoded)
        userid = userid_encoded.decode()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM todos where userid = %s",(userid,))
        data = cur.fetchall()
        cur.close()
        return str(data)
    else :
        return "login required!"

@app.route("/add-todo", methods=['POST'])
def add_todo():
    token = request.headers.get('Authorization')
    if token:
        token_encoded = token.encode()
        userid_encoded = token_gen.decrypt(token_encoded)
        userid = userid_encoded.decode()

        data = request.json
        title = data['title']
        cur = mysql.connection.cursor()
        cur.execute('insert into todos (userid,title) values (%s, %s)',(userid,title))
        mysql.connection.commit()
        cur.close()
        return 'ADDED!'
    else:
        return 'login required!'

@app.route("/register", methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password'].encode('utf-8')
    hashedPassword = bcrypt.hashpw(password, bcrypt.gensalt())
    cur = mysql.connection.cursor()
    cur.execute('insert into users (username, password) values (%s, %s)', (username, hashedPassword))
    mysql.connection.commit()
    cur.close()
    return 'registered'

@app.route("/login", methods = ['POST'])
def login():
    data = request.json

    username = data['username']
    password = data['password']
    password_encoded = password.encode('utf-8')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users where username = %s", (username,))
    data = cur.fetchone()
    cur.close()

    if data:
        password_fetched = data[2]
        password_fetched_encoded = password_fetched.encode()

        password_matched = bcrypt.checkpw(password_encoded, password_fetched_encoded)

        if password_matched:

            userid = str(data[0])
            userid_encoded = userid.encode()
            
            token = token_gen.encrypt(userid_encoded)
            token_plain = token.decode()


            return token_plain
        else:
            return 'Invalid credentials!'
    else:
        return "error!"
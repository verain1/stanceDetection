import time

import MySQLdb.cursors
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
import re

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'foodordering'
mysql = MySQL(app)
app.secret_key = "your secret key"


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    global opt1
    opt1 = True
    username = ""

    msg = ''
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session['loggedin'] = True
            session['id'] = 1
            session['username'] = "admin"
            session['fullname'] = "admin"
            session['age'] = 0
            session['phonenum'] = 0
            return render_template('upload.html')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = % s and password = % s', (username, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['fullname'] = account['fullname']
            session['age'] = account['age']
            session['phonenum'] = account['phonenum']

            return render_template('upload.html')

        else:
            msg = 'Incorrect username/ password'

    return render_template('login.html', msg=msg, login=username)


@app.route("/register", methods=["POST", "GET"])
def register():
    msg = ''
    username = ""
    fullname = ""
    phonenum = ""
    age = ""
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        phonenum = request.form['phonenum']
        age = request.form['age']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s', [username])
        account = cursor.fetchone()

        if not username or not password or not username or not fullname or not phonenum or not age:
            msg = 'Please fill out the form !'

        elif len(password) < 6:
            msg = 'Password must be over 5 characters long!'

        elif len(phonenum) != 10:
            msg = "Enter a valid phone number"
            phonenum = ""

        elif len(password) > 15:
            msg = 'Password must not be over 15 characters long!'

        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
            username = ""

        elif not re.search("[a-z]", password):
            msg = 'Password must contain atleast one lowercase letter!'

        elif not re.search("[A-Z]", password):
            msg = 'Password must contain atleast one uppercase letter!'

        elif not re.search("[0-9]", password):
            msg = 'Password must contain atleast one number!'

        elif re.search("[\s]", password):
            msg = 'Password cannot contain spaces'

        elif account:
            msg = 'Account already exists'

        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s)', [
                           fullname, username, phonenum, age, password])
            mysql.connection.commit()
            msg = 'You have successfully registered!'

    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg, user=username, full=fullname, phone=phonenum, a=age)

@app.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('fullname', None)
    session.pop('age', None)
    session.pop('password', None)

    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return render_template('upload.html')


@app.route('/data', methods=['GET', 'POST'])
def data():

    if request.method == 'POST':
        file = request.form['upload-file']
        global df
        df = pd.read_excel(file)
        reviews = df['reviews'].to_list()
        # return render_template('data.html', data=df.to_html())
        return render_template('data.html', data=reviews)


@app.route('/stance', methods=['GET', 'POST'])
def stance():
    global res
    global df
    res = []
    for i in df['reviews']:
        review = i
        review_vector = vectorizer.transform([review])
        res.append(classifier_linear.predict(review_vector)[0])
    df['stance'] = res
    df['stance'] = df['stance'].replace(['pos'], 'Favour')
    df['stance'] = df['stance'].replace(['neg'], 'Against')

    stances = df['stance'].to_list()
    reviews = df['reviews'].to_list()
    return render_template("stance.html", reviews=reviews, stances=stances)
    # return render_template("stance.html", stances=stances, reviews=reviews)


@app.route('/saveFile', methods=['GET', 'POST'])
def saveFile():
    file_name = "test.xlsx"
    df.to_excel(file_name)
    return render_template('saveFile.html')


if __name__ == "__main__":

    trainData = pd.read_csv(
        "https://raw.githubusercontent.com/Vasistareddy/sentiment_analysis/master/data/train.csv")
    testData = pd.read_csv(
        "https://raw.githubusercontent.com/Vasistareddy/sentiment_analysis/master/data/test.csv"
    )
    vectorizer = TfidfVectorizer(min_df=5,
                                 max_df=0.8,
                                 sublinear_tf=True,
                                 use_idf=True)
    train_vectors = vectorizer.fit_transform(trainData['Content'])
    test_vectors = vectorizer.transform(testData['Content'])
    classifier_linear = svm.SVC(kernel='linear')
    t0 = time.time()
    classifier_linear.fit(train_vectors, trainData['Label'])
    t1 = time.time()
    prediction_linear = classifier_linear.predict(test_vectors)
    t2 = time.time()
    time_linear_train = t1-t0
    time_linear_predict = t2-t1
    # results
    '''print("Training time: %fs; Prediction time: %fs" %
          (time_linear_train, time_linear_predict))
    report = classification_report(
        testData['Label'], prediction_linear, output_dict=True)
    print('positive: ', report['pos'])
    print('negative: ', report['neg'])
    review = "SUPERB, I AM IN LOVE IN THIS PHONE"
    review_vector = vectorizer.transform([review])  # vectorizing
    print(classifier_linear.predict(review_vector))'''
    app.run(debug=True)

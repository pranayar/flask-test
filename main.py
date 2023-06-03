from flask import Flask, render_template, request, redirect, url_for, session,jsonify,make_response
from flask_mysqldb import MySQL
from flask_session import Session
import MySQLdb.cursors
import re
import os
from datetime import datetime, timedelta

app = Flask(__name__)


app.config['SECRET_KEY'] = 'super secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'abcd6658'
app.config['MYSQL_DB'] = 'geeklogin'
app.config['SESSION_TYPE'] = 'filesystem'

mysql = MySQL(app)

@app.route('/')
def landing():
    if 'loggedin' in session:
        return redirect(url_for('post_login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM articles where assigned =0")
    data = cursor.fetchall()
    
    return render_template('index.html', data=data)

@app.route('/post_login', methods =['GET', 'POST'])
def post_login():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM articles where assigned = 0 or assigned=%s order by assigned desc",(session['id'],))
        data = cursor.fetchall()
        cursor.close()
        return render_template('list.html', data=data,name=session['name'])
    
    except:
        render_template("error.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('post_login'))
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE email = % s or mobileNo = % s AND password = % s', (username, username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['name'] = account['name']
            session.permanent = True  # Make the session permanent
            msg = 'Logged in successfully!'
            return redirect(url_for('post_login'))
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)

@app.route('/redirect-signup')
def redirect_signup():
    return redirect(url_for('signup'))

@app.route('/redirect-login')
def redirect_login():
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('name', None)
	return redirect(url_for('landing'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' and 'password' in request.form and 'email' in request.form :
		email = request.form['email']
		password = request.form['password']
		mob= request.form['mobile']
		name=request.form['name']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
  
		cursor.execute('SELECT * FROM accounts WHERE email = % s or mobileNo = %s', (email,mob, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		
		elif not password or not email:
			msg = 'Please fill out the form !'
		else:
			cursor.execute('INSERT INTO accounts(email,mobileNo,password,name) VALUES (%s, % s, % s, % s)', (email,mob,password,name))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('register.html', msg = msg)

@app.route('/reserve', methods =['GET','POST'])
def reserve():
    data = request.get_json()
    user = data['userId']
    article = data['articleId']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM articles WHERE assigned = %s', (user,))
    assigned = cursor.fetchone()
    if assigned:
        msg='0Kindly finish previous article0'
        
    else:
        cursor.execute("UPDATE articles SET assigned = %s,assignedTill=%s WHERE (idarticles = %s)",(user,datetime.now() + timedelta(hours=48),article))
        mysql.connection.commit()
        # msg='0Article assigned, complete by '+str(datetime.now())+'0'
        msg='0Article assigned, complete in 48 hours0'
        cancel_time = datetime.now() + timedelta(seconds=10)
        article_info = {'id': article, 'assigned': session['id']}
        
    cursor.close()
    response = {"message": msg}
    return jsonify(response=response)


@app.route('/submit_article', methods =['POST'])
def submit_article():
    if request.method == 'POST':  
        try:
            article_id = request.form.get('article_id')
            user= request.form.get('user_id')
            f = request.files['file']
            folder = 'wordDocuments'
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            file_path = os.path.join(folder, f.filename)
            f.save(file_path)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("UPDATE articles SET assigned = %s, doneBy =%s WHERE (idarticles = %s)",(-1,user,article_id,))
            mysql.connection.commit()
            cursor.close()
            
            return render_template("ack.html", fname = f.filename)  
        except:
            render_template("error.html")
            
        render_template("error.html")

@app.route('/cancel_article', methods =['POST'])
def cancel_article():
    if request.method == 'POST':  
        data = request.get_json()
        article_id = data['articleId']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE articles SET assigned = %s,assignedTill=%s WHERE (idarticles = %s)",(0,None,article_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('post_login'))

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))

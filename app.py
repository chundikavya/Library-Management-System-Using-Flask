from flask import Flask, render_template, request, redirect,session,url_for,flash
import mysql.connector
from flask_session import Session
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
app = Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'

# MySQL configurations
mydb=mysql.connector.connect(host="localhost",user="root",password="Mysql@pass!5",db="library_management")

#Routes
@app.route('/')
def index():
    return render_template('title.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=reuest.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/homepage')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('login'))
@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'password':password,'email':email}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['username'],data['password'],data['email']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
@app.route('/add_candidate', methods=['GET', 'POST'])
def add_books():
    if session.get('user'):
        if request.method == 'POST':
          id = request.form['id']
          title = request.form['title']
          author = request.form['author']
          cursor=mydb.cursor(buffered=True)
          cursor.execute('insert into candidates (id,title,author) values(%s,%s,%s)',[id, title,author])
          mydb.commit()
          cursor.close()
          return redirect('/books')
        return render_template('books.html')
    else:
        return redirect(url_for('login'))


@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
   
     id = request.form['id']
     title = request.form['title']
     author = request.form['author']
    # Insert feedback data into the database
     cursor=mydb.cursor()
     cursor.execute("INSERT INTO books (id,title,author) VALUES (%s, %s, %s)", (id,title,author))
     mydb.commit()
     return redirect(url_for('view'))
@app.route('/view')
def view():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from books')
        data=cursor.fetchall()      
        cursor.close()
        return render_template('index.html',data=data)
    else:
        return redirect(url_for('login'))

    # Retrieve all candidates from the database
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully loged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/history')
def history():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from usercalcount where username = %s order by cal_date desc',[username])
        data=cursor.fetchall()
        cursor.close()
        return render_template('history.html',data=data)
    else:
        return redirect(url_for('login'))
    
@app.route('/delete/<nid>')
def delete(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from userCalCount where cid=%s',[nid])
        mydb.commit()
        cursor.close()
        flash('Record Deleted.')
        return redirect(url_for('history'))
    else:
        return redirect(url_for('login'))
    
@app.route('/forgotpassword', methods=["GET","POST"])
def forgotpassword():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        confirmPassword = request.form['password1']
        if password != confirmPassword:
            flash('Both passwords are not same')
            return redirect(url_for('forgotpassword'))
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email from users where username=%s',[username])
        email = cursor.fetchone()[0]
        cursor.close()
        data={'username':username,'password':password, 'email':email}
        subject='Forgot Password Confirmation'
        body=f"Welcome to our Calorie Counter Application {username}!!!\n\nThis is your account's password reset confirmation email....\nClick on this link to confirm your reset password - {url_for('reset',token=token(data),_external=True)}\n\n\n\nWith Regards,\nCalorie Counter Team"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('forgotpassword'))
    return render_template('forgotpassword.html')

@app.route('/reset/<token>')
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception:
        flash('Link expired reset your password again')
        return redirect(url_for('forgotpassword'))
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        password = data['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update users set password = %s where username = %s',[password, username])
        mydb.commit()
        cursor.close()
        flash('Password Reset Successful!')
        return redirect(url_for('login'))

app.run(debug=True,use_reloader=True)

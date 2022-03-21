######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'prxthana'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		f_name = request.form.get('first name')
		l_name = request.form.get('last name')
		dob = request.form.get('date of birth')
		gender = request.form.get('gender')
		hometown = request.form.get('hometown')

	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, birth_date, gender, hometown) \
		VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, f_name, l_name, dob, gender, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=user.id, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

## ANOTHER NEW FUNCTION TO GET ALBUMS !!!! 
def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

# Helper method to make sure a user only views/edits albums that actually exist
def isValidAlbum(album_name, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM ALBUMS WHERE user_id = '{0}' AND name = '{1}'".format(uid, album_name)):
	   return True
	else:
		return False

#Function to display friend list
def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name FROM (SELECT user_id2 FROM Friends WHERE user_id1 = '{0}') AS List LEFT JOIN Users on Users.user_id = List.user_id2".format(uid))
	return cursor.fetchall()

def isValidFriend(friend_name, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id2 FROM FRIENDS WHERE user_id1 = '{0}' AND user_id2 = '{1}'".format(uid, friend_name)):
	   return True
	else:
		return False

def isValidUser(friend):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Users WHERE email = '{0}'".format(friend)):
	   return True
	else:
		return False

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# NEW STUFF!!!
@app.route('/album', methods=['POST'])
@flask_login.login_required
def manange_album():

	# option 1: user is creating an album
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	name = request.form.get('album')
	date = request.form.get('date')
	if name != None and date != None:
		cursor.execute('''INSERT INTO Albums (user_id, name, date) VALUES (%s, %s, %s)''', (uid, name, date))
		conn.commit()
		return render_template('album.html', name=flask_login.current_user.id, message='Album Created!', albums=getUsersAlbums(uid))

	# option 2: user is deleting an album
	to_delete = request.form.get('album_to_delete')
	if to_delete != None:
		cursor.execute('''DELETE FROM Albums WHERE user_id = %s AND name = %s''', (uid, to_delete))
		conn.commit()
		return render_template('album.html', name=flask_login.current_user.id, message='Album Deleted!', albums=getUsersAlbums(uid))
	
	view = request.form.get('view_album')
	print("view is:", view)
	if view != None:
		valid_album = isValidAlbum(view, uid)
		print("is the album valid?", valid_album)
		if valid_album:
			return render_template('upload.html', name=flask_login.current_user.id, album_name=view)
		else:
			return render_template('album.html', name=flask_login.current_user.id, message='Not a valid album name. Try again.', albums=getUsersAlbums(uid))

	# if they're not executing either options then just show their albums
	return render_template('album.html', name=flask_login.current_user.id, albums=getUsersAlbums(uid))

	
@app.route('/album', methods=['GET'])
@flask_login.login_required
def display_albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	try_albums = getUsersAlbums(uid)
	return render_template('album.html', albums=try_albums)

@app.route('/friends', methods=['POST'])
@flask_login.login_required
def manage_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	search = request.form.get('search_friends')

	if search != None:
		valid_user = isValidUser(search)
		if valid_user:
			friend_uid = getUserIdFromEmail(search)
			cursor.execute('''INSERT INTO Friends (user_id1, user_id2) VALUES (%s, %s)''', (uid, friend_uid))
			conn.commit()
			return render_template('friends.html', name=flask_login.current_user.id, message=f'You are now friends with {search}', friends=getUsersFriends(uid), friend=search)
		else:
			return render_template('friends.html', name=flask_login.current_user.id, message='Not a valid friend name. Try again.', friends=getUsersFriends(uid), friend=search)

	return render_template('friends.html', name=flask_login.current_user.id, friends=getUsersFriends(uid), friend=search)

@app.route('/friends', methods=['GET'])
@flask_login.login_required
def display_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friends.html', friends=getUsersFriends(uid))

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

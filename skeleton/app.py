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
		#return flask.redirect(flask.url_for('register'))
		#return render_template('hello.html', message='Try another email, this email is already linked to an account')
		return "<a href='/register'>Try again. This email is already registered for another account</a>"

def getUsersPhotos(uid, album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}' AND albums_id = '{1}'".format(uid, album_id))
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

# Helper method to get a user's albums
def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

# Helper method to make sure a user only views/edits albums that actually exist
def getAlbumID(album_name, uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT albums_id FROM Albums WHERE user_id = %s AND name = %s LIMIT 1''', (uid,album_name))
	a_id = cursor.fetchall()[0][0]
	return a_id
  
# helper method that checks if a tag already exists, and if it doesn't adds it to the DB
def doesTagExist(tag_name):
	cursor = conn.cursor()
	if cursor.execute("SELECT Tags.tag_id FROM Tagged, Tags WHERE Tagged.tag_id = Tags.tag_id AND Tags.name = '{0}'".format(tag_name)):
		return cursor.fetchone()[0]
	else:
		# add the tag_name to tags!
		cursor.execute('''INSERT INTO Tags (name) VALUES (%s)''', tag_name)
		conn.commit()
		cursor.execute('''SELECT tag_id FROM Tags WHERE name = %s''', tag_name)
		return cursor.fetchone()[0]

def user_tags(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT Tags.name FROM Tagged, Tags WHERE Tagged.tag_id = Tags.tag_id AND Tagged.photo_id IN 
	(SELECT photo_id FROM Photos WHERE user_id = %s)''', uid)
	return cursor.fetchall()

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

def getLikes():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id, first_name FROM Likes, Users WHERE Users.user_id = Likes.user_id")
	return cursor.fetchall()

#recommendation function
def getFriendRecommendation(uid):
	query = '''
		SELECT email FROM 
		(SELECT DISTINCT user_id2, COUNT(*)
		FROM Friends 
		WHERE user_id1 
		IN 
			(SELECT user_id2 
			FROM Friends 
			WHERE user_id1 = '{0}')
		AND user_id2
		NOT IN
			(SELECT user_id2 
			FROM Friends 
			WHERE user_id1 = '{0}')
		GROUP BY user_id2
		ORDER BY COUNT(*) DESC) AS list1 LEFT JOIN USERS ON Users.user_id = list1.user_id2'''.format(uid)
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

#comment helper functions
def getCommentID(photo_id, uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT comment_id FROM Comments WHERE photo_id = %s AND user_id = %s LIMIT 1''', (photo_id, uid))
	c_id = cursor.fetchall()[0]
	print("THIS IS THE COMMENT ID", c_id)
	return c_id

def getPhotoComments():
	cursor = conn.cursor()
	cursor.execute('''SELECT first_name, photo_id, text FROM (SELECT photo_id, user_id, text FROM Comments) as info LEFT JOIN Users on Users.user_id = info.user_id;
''')

	return cursor.fetchall()

#contribution helper function
def getUsersContibutionScore(uid):
	query = ''' 
	SELECT email FROM
	(SELECT a.user_id, (a.cnt + b.cnt) as C
	FROM (SELECT Photos.user_id, COUNT(*) as cnt
		FROM Photos
		GROUP BY user_id) AS a LEFT JOIN
		(SELECT Comments.user_id, COUNT(*) as cnt
 		FROM Comments
 		GROUP BY user_id) AS b ON a.user_id = b.user_id)
	as sum LEFT JOIN USERS ON Users.user_id = sum.user_id
	ORDER BY C DESC
	LIMIT 10'''

	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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
	
	# if they're not any options then just show their albums
	return render_template('album.html', name=flask_login.current_user.id, albums=getUsersAlbums(uid))

@app.route('/contributions', methods=['GET'])
@flask_login.login_required
def display_contributions():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	contribution_scores = getUsersContibutionScore(uid)
	return render_template('contributions.html', name=flask_login.current_user.id, scores=contribution_scores)

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
			return render_template('friends.html', name=flask_login.current_user.id, message=f'You are now friends with {search}', friends=getUsersFriends(uid), friend=search, recs = getFriendRecommendation(uid))
		else:
			return render_template('friends.html', name=flask_login.current_user.id, message='Not a valid friend name. Try again.', friends=getUsersFriends(uid), friend=search, recs = getFriendRecommendation(uid))
	
	return render_template('friends.html', name=flask_login.current_user.id, friends=getUsersFriends(uid), friend=search, recs = getFriendRecommendation(uid))

@app.route('/friends', methods=['GET'])
@flask_login.login_required
def display_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friends.html', friends=getUsersFriends(uid), recs = getFriendRecommendation(uid))

# browsing photos - for anyone visiting the site even if not registered
@app.route('/browse', methods=['GET', 'POST'])
def all_photos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos")
	return render_template('browse.html', photos=cursor.fetchall(), comms=getPhotoComments(), likes=getLikes(), base64=base64)

@app.route('/like/<photo_id>', methods=['POST'])
def like_photo(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos")
	all_photos = cursor.fetchall()

	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		return render_template('browse.html', message="ERROR! You are not signed in so you cannot like any photos", photos=all_photos, comms=getPhotoComments(), likes=getLikes(), base64=base64)

	# check that the user didn't already like the photo 
	if cursor.execute("SELECT * FROM LIKES WHERE user_id = '{0}' AND photo_id = '{1}'".format(uid, photo_id)):
		return render_template('browse.html', message="ERROR - You already liked this photo!", photos=all_photos, comms=getPhotoComments(), likes=getLikes(), base64=base64)
	
	# add it to the likes relation
	cursor.execute("INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)", (uid, photo_id))
	conn.commit()
	return render_template('browse.html', message="success!", photos=all_photos, comms=getPhotoComments(), base64=base64, likes=getLikes())


#Comment Code
@app.route('/comments/<photo_id>', methods=['POST'])
def manage_comments(photo_id):
	cursor = conn.cursor()
	cursor.execute('''SELECT data, photo_id, caption FROM Photos''')
	all_photos = cursor.fetchall()
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		uid = None
		pass
	comment = request.form.get('comment')
	
	if uid == None:
		cursor.execute('''INSERT INTO Comments (photo_id, text) VALUES (%s, %s)''', (photo_id, comment))
		conn.commit()
		message = 'new comment made!'

	else:
			# check that the user isn't commenting on their own photo
		if cursor.execute('''SELECT * FROM PHOTOS WHERE photo_id = %s AND user_id = %s''', (photo_id, uid)):
			message = 'Error - you cannot comment photos that you upload!'
		else:
			cursor.execute('''INSERT INTO Comments (photo_id, user_id, text) VALUES (%s, %s, %s)''', (photo_id, uid, comment))
			conn.commit()
			message = 'new comment made!'
	
	return render_template('browse.html', message=message, comms = getPhotoComments(), photos=all_photos, likes=getLikes(), base64=base64)
	
# deleting a photo OR adding a tag to a photo
@app.route('/upload/<action>/<photo_id>/<album_name>/', methods=['POST'])
@flask_login.login_required
def delete_or_add_tag(action, photo_id, album_name):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	a_id = getAlbumID(album_name, uid)
	cursor = conn.cursor()

	# delete a photo 
	if action == 'delete':
		cursor.execute('''DELETE FROM Photos WHERE photo_id = %s''', (photo_id))
		conn.commit()
		return render_template('upload.html', message='Photo Deleted', album_name=album_name, photos=getUsersPhotos(uid,a_id), base64=base64)
	
	# add a tag
	else: 
		tag = request.form.get('tag')	
		# call helper function
		tag_id = doesTagExist(tag)
		# then need to add photo, tag into the tagged DB 
		cursor.execute('''INSERT INTO TAGGED (photo_id, tag_id) VALUES (%s, %s)''', (photo_id, tag_id))
		conn.commit()
		return render_template('upload.html', message='tag added!', album_name=album_name, photos=getUsersPhotos(uid,a_id), base64=base64)


@app.route('/upload/<album_name>', methods=['POST'])
@flask_login.login_required
def upload_file(album_name):
	
	uid = getUserIdFromEmail(flask_login.current_user.id)
	a_id = getAlbumID(album_name, uid)
	cursor = conn.cursor()
	# uploading a photo
	
	caption = request.form.get('caption')
	
	imgfile = request.files['photo']
	photo_data =imgfile.read()
	
	cursor.execute('''INSERT INTO Photos (data, user_id, caption, albums_id) VALUES (%s, %s, %s, %s)''', (photo_data, uid, caption, a_id))
	conn.commit()
	return render_template('upload.html', name=flask_login.current_user.id, message='Photo uploaded!',
		album_name=album_name, photos=getUsersPhotos(uid,a_id), base64=base64)
		

@app.route('/upload/<album_name>', methods=['GET'])
@flask_login.login_required
def album_details(album_name):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	a_id = getAlbumID(album_name, uid)
	return render_template('upload.html', album_name=album_name, photos=getUsersPhotos(uid,a_id), base64=base64)
#end photo uploading code

# viewing tags 
@app.route("/tags/<tag>/<view>", methods=['GET', 'POST'])
@flask_login.login_required
def see_tagged_photos(tag, view):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	# get the tag id of that tag 
	
	tag_id = doesTagExist(tag)

	# if view is default, then let them choose if they want to see user photos 
	# with tag or ALL photos with that tag 
	if view == 'default':
	   return render_template('tags.html', default=view, tag=tag)

	elif view == 'userview':
	# get the user's photos with that tag
		cursor.execute("SELECT data, Photos.photo_id, caption FROM Tagged, Photos WHERE Tagged.photo_id = Photos.photo_id AND tag_id = '{0}' \
		AND Photos.photo_id IN (SELECT photo_id FROM PHOTOS WHERE user_id = '{1}')".format(tag_id, uid))
		user_pics = cursor.fetchall()
		return render_template('tags.html', tag=tag, userview=view, user_photos=user_pics, base64=base64)

	elif view == 'all':
		cursor.execute("SELECT P.data, P.photo_id, P.caption FROM PHOTOS P WHERE P.photo_id IN \
		(SELECT photo_id FROM Tagged WHERE tag_id = %s)", tag_id)
		all_pics = cursor.fetchall()
		
		return render_template('tags.html', tag=tag, all=view, all_photos=all_pics, base64=base64)

# most popular tag function
@app.route("/tags/<view>", methods=['GET', 'POST'])
def most_popular_tags(view):
	cursor = conn.cursor()
	cursor.execute("SELECT Tags.name, COUNT(*) AS photocount FROM Tagged, Tags \
	WHERE Tags.tag_id = Tagged.tag_id GROUP BY Tags.name ORDER BY photocount DESC")
		
	# "SELECT COUNT(*), tag_id FROM Tagged GROUP BY tag_id ORDER BY tag_id DESC")
	names = cursor.fetchall()
	return render_template('tags.html', most_popular=view,names=names )
	
@app.route("/tag", methods=['GET'])
def tag_home():
	return render_template('tag.html')

@app.route("/tag", methods=['POST'])
def tag_home_two():
	cursor = conn.cursor()
	search_for = request.form.get('tag').split()
	if len(search_for) == 1:
		# search for that one tag
		if cursor.execute("SELECT Tags.tag_id FROM Tagged, Tags WHERE Tagged.tag_id = Tags.tag_id AND Tags.name = '{0}'".format(search_for[0])):
		   tag_id_1 = cursor.fetchone()[0]
		   cursor.execute("SELECT data, Photos.photo_id, caption FROM Tagged, Photos WHERE Tagged.photo_id = Photos.photo_id AND tag_id = '{0}'".format(tag_id_1))
		   results = cursor.fetchall()
		   return render_template('tag.html', tag=search_for[0], photos=results, base64=base64)
		else:
			return render_template('tag.html', message="That tag doesn't exist in the DB")
			 
	if len(search_for) != 2:
		return render_template('tag.html', message="Error! You must enter two tags separated by a space")
	tag_id_1 = None
	tag_id_2 = None


	if cursor.execute("SELECT Tags.tag_id FROM Tagged, Tags WHERE Tagged.tag_id = Tags.tag_id AND Tags.name = '{0}'".format(search_for[0])):
		tag_id_1 = cursor.fetchone()[0]
	
	if cursor.execute("SELECT Tags.tag_id FROM Tagged, Tags WHERE Tagged.tag_id = Tags.tag_id AND Tags.name = '{0}'".format(search_for[1])):
		tag_id_2 = cursor.fetchone()[0]
	
	if tag_id_1 != None and tag_id_2 != None:
		query = "SELECT data, Photos.photo_id, caption FROM Photos WHERE Photos.photo_id \
		IN (SELECT Ta1.photo_id FROM Tags T1, Tagged Ta1, Tags T2, Tagged Ta2 WHERE \
		T1.tag_id = Ta1.tag_id AND T2.tag_id = Ta2.tag_id AND T1.tag_id = '{0}' AND T2.tag_id='{1}')"

		cursor.execute(query.format(tag_id_1, tag_id_2))
		results = cursor.fetchall()

		return render_template('tag.html', tag=search_for, photos=results, base64=base64)
	
	if tag_id_1 == None or tag_id_2 == None:
		message = "at least one of the tags you entered doesn't exist in the DB"
	else:
		message = "there are no photos in the DB with both the tags " + search_for[0] + " and" + search_for[1]
	
	return render_template('tag.html', message=message)

@app.route("/tagalbums", methods=['GET', 'POST'])
@flask_login.login_required
def view_all_tagalbums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	tags=user_tags(uid)
	return render_template('tagalbums.html', tags=tags)
	

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

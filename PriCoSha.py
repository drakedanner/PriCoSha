#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='test',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
	return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	username = request.form['username']
	password = request.form['password']
	password = hashlib.md5(password).hexdigest()
	cursor = conn.cursor()
	query = 'SELECT * FROM Person WHERE username = %s and password = %s'
	cursor.execute(query, (username, password))
	data = cursor.fetchone()
	cursor.close()
	error = None
	if(data):
		session['username'] = username
		return redirect(url_for('home'))
	else:
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	username = request.form['username']
	password = request.form['password']

	password = hashlib.md5(password).hexdigest()

	cursor = conn.cursor()
	query = 'SELECT * FROM Person WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchone()
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO Person VALUES(%s, %s, null, null)'
		cursor.execute(ins, (username, password))
		conn.commit()
		cursor.close()
		return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT content_name, file_path, timest FROM Content WHERE username = %s ORDER BY timest DESC'
    cursor.execute(query, (username))
    data = cursor.fetchall()

    #later: add in query for all public posts

    groupsIn = []
    query2 = 'SELECT group_name FROM Member WHERE username = %s or username_creator = %s'
    cursor.execute(query2, (username,username))
    print(cursor.fetchall())
    #groupsIn.append(cursor.fetchone()) #causing issue

    displayData = []
    for i in groupsIn:
        newQuery = "SELECT name, file_path, timest FROM Content NATURAL JOIN Share NATURAL JOIN FriendGroup WHERE group_name = %s"
        cursor.execute(newQuery, (i))
        displayData.append(cursor.fetchall())

    cursor.close()
    return render_template('home.html', username=username, myPosts=data, groupPosts = displayData)


@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	blog = request.form['blog']
	query = 'INSERT INTO Content (ctext, username) VALUES(%s, %s)'
	cursor.execute(query, (blog, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))



@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')

@app.route('/createGroup', methods=['GET', 'POST'])
def createGroup():
	return render_template('createGroup.html')

@app.route('/createGroupAction', methods=['GET', 'POST'])
def createGroupAction():
	username = session['username']
	group_name = request.form['groupName']
	description = request.form['description']

	cursor = conn.cursor()

	query = "INSERT INTO FriendGroup VALUES(%s, %s, %s)"
	cursor.execute(query, (group_name, username, description))
	conn.commit()
	cursor.close()
	return render_template('home.html')

@app.route('/addFriend', methods =['GET','POST'])
def addFriend():
	return render_template('addFriend.html')

@app.route('/addFriendAction', methods =['GET','POST'])
def addFriendAction():
	friendUsername = request.form['friendName']
	friendGroup = request.form['friendGroup']
	creatorName = session['username']

	cursor = conn.cursor()

	query = "INSERT INTO Member VALUES(%s, %s, %s)"
	cursor.execute(query, (friendUsername, friendGroup, creatorName))
	conn.commit()
	cursor.close()
	return render_template('home.html')

@app.route('/addContent', methods =['GET', 'POST'])
def addContent():
	return render_template('addContent.html')

@app.route('/addContentAction', methods =['GET', 'POST'])
def addContentAction():
	username = session['username']
	title = request.form['contentTitle']
	link = request.form['link']
	status = request.form['status']
	cursor = conn.cursor()
	query = "INSERT INTO Content (username, file_path, content_name, public) VALUES(%s, %s, %s, %s)"
	if status == "private":
		cursor.execute(query, (username, link, title, False))
		conn.commit()
        #cursor.close()

        #adding in privacy setting specific code
        groupsQuery = "SELECT group_name FROM Member WHERE username_creator = %s"
        cursor.execute(groupsQuery, (username))
        groupsIn = cursor.fetchall()
        return render_template('privacySettings.html', groupsIn = groupsIn)

    # else:
    #     # indentation error?
    #     cursor.execute(query, (username, link, title, True))
    #     conn.commit()
    #     cursor.close()

        # return render_template('home.html')

@app.route('/viewGroups', methods =['GET', 'POST'])
def viewFriendGroups():
    username = session['username']
    query1 = "SELECT group_name FROM Member WHERE username_creator = %s"
    query2 = "SELECT group_name FROM Member WHERE username = %s"
    cursor = conn.cursor()
    cursor.execute(query1, (username))
    owned = cursor.fetchall()
    cursor.execute(query2, (username))
    included = cursor.fetchall()
    cursor.close()
    return render_template("viewGroups.html", owned = owned, included = included)

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)

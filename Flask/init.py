#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       #port = 8889,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Login/Register - Show public posts that are posted within 24 hours
@app.route('/')
def hello():
    cursor = conn.cursor();
    query = 'SELECT * FROM contentitem WHERE is_pub AND TIMESTAMPDIFF(HOUR, post_time, CURRENT_TIMESTAMP)<=24'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', public=data)

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Login into Pricosha
@app.route('/loginAuth', methods=['GET', 'POST'])   
def loginAuth():    
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    
    #query from database
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE email = %s and password = %s'
    hashed_pwd = hashlib.sha256(password.encode()).hexdigest() # hash the password
    cursor.execute(query, (email, hashed_pwd))
    
    #stores the results in a variable
    data = cursor.fetchone() #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user session is a built in
        session['email'] = email
        session['fname'] = data['fname']
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('index.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, hashed_pwd, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')

#Display shared posts and public posts
@app.route('/home')     
def home(error = None):
    user = session['email']
    cursor = conn.cursor();
    
    # Find the posts that are shared with user
    query = 'SELECT * FROM contentitem WHERE email_post IN (SELECT DISTINCT email FROM share NATURAL JOIN belong WHERE email = %s OR owner_email = %s) OR'
    query += '(is_pub AND TIMESTAMPDIFF(HOUR, post_time, CURRENT_TIMESTAMP)<=24) ORDER BY post_time DESC'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    
    infoString = []
    for entry in data:
        append = {"post":entry}
        query = 'SELECT fname, lname FROM person NATURAL JOIN (SELECT email_tagged AS email FROM tag WHERE item_id=%s AND status = "accept") AS T'
        cursor.execute(query, entry['item_id'])
        taggees = cursor.fetchall()
        tagStr = "TAGGEE(s): |"
        if (taggees):
            for person in taggees:
                tagStr += (person['fname']+ " "+ person['lname']+ "|")
        else:
            tagStr += "None|"
        append["taggee"]=tagStr
        
        query = "SELECT emoji FROM rate WHERE item_id=%s"
        cursor.execute(query, entry['item_id'])
        emojis = cursor.fetchall()
        emojiStr = "RATING(s): |"
        if (emojis):
            for emoji in emojis:
                emojiStr += (emoji['emoji'] + "|")
        else:
            emojiStr += "None|"
        append["emoji"]=emojiStr
        infoString.append(append)
    cursor.close()
    
    return render_template('home.html', name=session['fname'], info=infoString, error=error)

@app.route('/post', methods=["GET", "POST"])
def post():
    email = session['email']
    isPub = request.form['isPub']
    itemName = request.form['itemName']
    filePath = request.form['filePath']
    if (filePath == ''):
        filePath = None
    cursor = conn.cursor();
    # Can always insert because item_id will update itself
    query = 'INSERT INTO ContentItem VALUES(NULL, %s, CURRENT_TIMESTAMP, %s, %s, %s)'
    cursor.execute(query, (email, filePath, itemName, isPub))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/tag', methods=["GET", "POST"])
def tag():
    email = session['email']
    tagEmail = request.form['email']
    itemID = request.form['itemID']
    
    cursor = conn.cursor();
    query = "SELECT * FROM person WHERE email = %s "
    cursor.execute(query, tagEmail)
    data = cursor.fetchone()
    cursor.close()
    if not (data):
        error = "Cannot process tag - this user does not exist"
        return home(error)
    
    cursor = conn.cursor();
    query = "SELECT * FROM contentitem WHERE item_id = %s AND (email_post IN "
    query += "(SELECT DISTINCT email FROM share NATURAL JOIN belong WHERE email = %s OR owner_email = %s) OR "
    query += "is_pub AND TIMESTAMPDIFF(HOUR, post_time, CURRENT_TIMESTAMP)<=24) "
    cursor.execute(query, (itemID, tagEmail, tagEmail))
    data = cursor.fetchone()
    cursor.close()
    if not (data):
        error = "Cannot process tag - content item not visible to this user"
        return home(error)
    
    cursor = conn.cursor();
    query = "SELECT * FROM tag WHERE email_tagger = %s AND email_tagged = %s AND item_id = %s"
    cursor.execute(query, (email, tagEmail, itemID))
    data = cursor.fetchone()
    if(data):
        cursor.close()
        error = "Cannot process tag - this user has been tagged"
        return home(error)
    
    ins = "INSERT INTO tag VALUES "
    if (email == tagEmail):
        ins += '(%s, %s, %s, "accept", CURRENT_TIMESTAMP)'
    else:
        ins += '(%s, %s, %s, "false", CURRENT_TIMESTAMP)'
    cursor.execute(ins, (tagEmail, email, itemID))
    conn.commit()
    cursor.close()
    return home()

@app.route('/rate', methods=["GET", "POST"])
def rate():
    email = session['email']
    emoji = request.form['emoji']
    itemID = request.form['itemID']
    
    cursor = conn.cursor();
    query = "SELECT * FROM rate WHERE email = %s AND item_id = %s "
    cursor.execute(query, (email, itemID))
    data = cursor.fetchone()
    if (data):
        cursor.close()
        error = "Cannot process rate - one rating per content item"
        return home(error)
    
    query = "INSERT INTO rate VALUES (%s, %s, CURRENT_TIMESTAMP, %s) "
    cursor.execute(query, (email, itemID, emoji))
    conn.commit()
    cursor.close()
    return home()

@app.route('/friend_group', methods=["GET", "POST"])
def friend_group(error = None):
    email = session['email']
    cursor = conn.cursor();
    query = 'SELECT * FROM friendgroup WHERE owner_email= %s '
    cursor.execute(query, email)
    myGroup = cursor.fetchall()
    for group in myGroup:
        query = "SELECT fname, lname FROM belong NATURAL JOIN person WHERE fg_name = %s AND owner_email = %s ORDER BY fname"
        cursor.execute(query, (group["fg_name"], group["owner_email"]))
        member = cursor.fetchall()
        group['member'] = member
    
    query = 'SELECT * FROM belong WHERE email = %s AND owner_email != %s '
    cursor.execute(query, (email, email))
    otherGroup = cursor.fetchall()
    for group in otherGroup:
        query = "SELECT fname, lname FROM belong NATURAL JOIN person WHERE fg_name = %s AND owner_email = %s ORDER BY fname"
        cursor.execute(query, (group["fg_name"], group["owner_email"]))
        member = cursor.fetchall()
        group['member'] = member
    
    query = 'SELECT * FROM contentitem WHERE email_post = %s AND !is_pub '
    cursor.execute(query, email)
    posts = cursor.fetchall()
    cursor.close()
    
    return render_template('friend_group.html', name=session['fname'], myGroup = myGroup, otherGroup = otherGroup, posts = posts, error = error)

@app.route('/add_group', methods=["GET", "POST"])
def add_group():
    email = session['email']
    fgName = request.form['fgName']
    des = request.form['des']
    if (des == ''):
        des = None
    cursor = conn.cursor();
    query = "SELECT * FROM friendgroup WHERE owner_email = %s AND fg_name = %s "
    cursor.execute(query, (email, fgName))
    data = cursor.fetchone()
    if (data):
        cursor.close()
        error = "Cannot process add group - cannot have two groups with the same name"
        return friend_group(error)
    #INSERT INTO friendgroup (`owner_email`, `fg_name`, `description`) VALUES (,,,);
    query = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
    cursor.execute(query, (email, fgName, des))
    conn.commit()
    cursor.close()
    return redirect(url_for('friend_group'))

@app.route('/share_post', methods=["GET", "POST"])
def share_post():
    ownerEmail = request.form['groups'].split(',')[0]
    fgName = request.form['groups'].split(',')[1]
    itemID = request.form['itemID']
    cursor = conn.cursor();
    try: 
        query = "INSERT INTO share VALUES (%s, %s, %s)"
        cursor.execute(query, (fgName, ownerEmail, itemID))
        conn.commit()
        cursor.close()
        return redirect(url_for('friend_group'))
    except pymysql.err.IntegrityError:
        error = "Cannot process share - already shared with this group"
        return friend_group(error)
    
@app.route('/add_friend', methods=["GET", "POST"])
def add_friend():
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    ownerEmail = session['email']
    fgName = request.form['fgName']
    cursor = conn.cursor();
    if (email == ''):
        query = "SELECT * FROM person WHERE fname = %s AND lname = %s"
        cursor.execute(query, (fname, lname))
    else:
        query = "SELECT * FROM person WHERE fname = %s AND lname = %s AND email = %s"
        cursor.execute(query, (fname, lname, email))
    person = cursor.fetchall()
    # Does this person exist
    if not (person):
        cursor.close()
        error = "Cannot process add - this user does not exist"
        return friend_group(error)
    # Multiple people with the same name
    if (len(person) > 1):
        cursor.close()
        error = "Cannot process add - multiple people with the same name, try include email"
        return friend_group(error)
    # Has been tagged
    email = person[0]['email']
    query = 'SELECT * FROM belong WHERE email = %s AND owner_email = %s AND fg_name = %s '
    cursor.execute(query, (email, ownerEmail, fgName))
    data = cursor.fetchall()
    if (data):
        error = "Cannot process add - this user has been added"
        return friend_group(error)
    #INSERT INTO `belong` (`email`, `owner_email`, `fg_name`) VALUES ('m', 'm', 'm');
    query = 'INSERT INTO belong VALUES (%s, %s, %s)'
    cursor.execute(query, (email, ownerEmail, fgName))
    conn.commit()
    cursor.close()
    return friend_group()

@app.route('/manage_tags', methods=["GET", "POST"])
def tag_requests():
    #query from database
    cursor = conn.cursor();
    query = 'SELECT * FROM tag WHERE email_tagged = %s AND status = "false"'
    cursor.execute(query, session['email'])
    data = cursor.fetchall()
    cursor.close()
    
    return render_template('manage_tags.html', data = data)

@app.route('/update_tagged', methods=['GET', 'POST'])
def update_tags():
    #grabs information from the forms
    itemID = request.form['itemID']
    tagger = request.form['tagger']
    
    #query from database
    cursor = conn.cursor()
    query = 'UPDATE tag SET status = "accept" WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s;'
    cursor.execute(query, (session['email'], tagger, itemID))
    conn.commit()
    cursor.close()
    
    return tag_requests()

@app.route('/remove_tagged', methods=['GET', 'POST'])
def remove_tags():
    #grabs information from the forms
    itemID = request.form['itemID']
    tagger = request.form['tagger']
    
    #query from database
    cursor = conn.cursor()
    query = 'UPDATE tag SET status = "decline" WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s;'
    cursor.execute(query, (session['email'], tagger, itemID))
    conn.commit()
    cursor.close()
    
    return tag_requests()

@app.route('/logout')
def logout():
    session.pop('email')
    session.pop('fname')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
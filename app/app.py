from datetime import datetime
from flask import Flask, request, render_template, redirect, session, url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import pytz
import os
from dotenv import load_dotenv
import logging

load_dotenv()  # load environment variables form .env

'''
NB: Chossing a logging levels logs that level and all subsequent levels
logging levels:
logging.DEBUG
logging.INFO
logging.WARNING
logging.ERROR
logging.CRITICAL
'''

logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(filename='log/record.log', filemode='w',format=FORMAT)
logger.setLevel(logging.WARNING)

# create Flask app
app = Flask(__name__)
app.secret_key = "REDACTED"

# user credentials
# credentials = {'john':'123', 'amy': '123', 'admin':'admin'}

# read first name and password from table into tuple
# register method does not allow for two people with the same username
# therefore this method returns a tuple containing information from one row of a table


def get_credentials_tuple(email):
    myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
        'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

    cur = myconn.cursor()
    try:
        
        query = 'SELECT coach_name, coach_password FROM coach WHERE coach_email = "' + email + '";'
        cur.execute(query)
        myresult1 = cur.fetchone()

        query = 'SELECT coachee_name, coachee_password FROM coachee WHERE coachee_email = "' + email + '";'
        cur.execute(query)
        myresult2 = cur.fetchone()

    except:
        myresult1 = None
        myresult2 = None
        myconn.rollback()

    myconn.close()

    # They have not registered
    if ((myresult1 == None) and (myresult2 == None)):
        return myresult1
    # They are a coach
    elif ((myresult1 != None) and (myresult2 == None)):
        # store user type in a cookie
        session['user_type'] = 'coach'
        return myresult1
    # They are a coachee
    elif ((myresult1 == None) and (myresult2 != None)):
        # store user type in a cookie
        session['user_type'] = 'coachee'
        return myresult2

def ifEmailExists(email):
    myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
        'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

    cur = myconn.cursor()
    try:
        query = 'SELECT coach_email FROM coach WHERE coach.coach_email = "' + email + '" UNION SELECT coachee_email FROM coachee WHERE coachee_email = "' + email + '";'
        cur.execute(query)
        myresult = cur.fetchone()

    except:
        myresult = None
        myconn.rollback()

    myconn.close()

    if myresult is None:
        return False
    else:
        return True
    

# index page


@app.route('/', methods=["GET", "POST"])
def landingPage():
    return render_template('welcome.html')

# login page


@app.route('/home')
def success():
    # create_rating(5, 'test@gmail.com')
    return render_template('home.html')

# TODO: Change how you pass the email in when making the dropdown

@app.route('/login', methods=["GET", "POST"])
def login():

    # retrieve info from login form
    if request.method == 'POST':
        login_email = request.form.get("email")
        login_password = request.form.get('user_password')

        my_tuple = get_credentials_tuple(login_email)
        # check if the email entered is registered in the database
        if my_tuple != None:
            # check if the password entered matches up to the hashed password in the database
            if check_password_hash(my_tuple[1], login_password):

                # store login information on a cookie
                session['email'] = login_email

                logger.warning('Logged in Succesfully!')
                return redirect(url_for('success'))
            else:
                # failed login
                logger.warning('Incorrect password, try again!')
                return render_template('login.html', error_msg = "Incorrect password, try again.")
        else:
            # failed login
            logger.warning('User has not registered yet!')
            return render_template("login.html", error_msg = "User has not registered yet")
            

    return render_template('login.html')

# code to log user out


@app.route('/logout', methods=["GET", "POST"])
def logout():
    try:
        # check if user is logged in
        if session['username']:

            # log user out
            session.pop('username', default=None)
            session.pop('email', default=None)
            session.pop('user_type', default=None)
            
        return redirect('/')
    except:
        return redirect('/')

# recieve information from html form


@app.route('/register', methods=["GET", "POST"])
def register():
    session['register'] = 'registered'

    if request.method == 'POST':
        textName = request.form.get('first-name')
        textLName = request.form.get('last-name')
        textEmail = request.form.get('email')
        textPassword = request.form.get('new-password')
        userType = ''

        if 'coach1' in request.form:
            userType = 'coach'
        else:
            userType = 'coachee'

        emailExists = ifEmailExists(textEmail)

        # check if the username exists in the db yet
        if emailExists == False:

            # hash password
            passwordHash = generate_password_hash(textPassword)

            # commit info to mysql
            myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
                'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

            cur = myconn.cursor()

            query = 'INSERT INTO ' + userType + ' (' + userType + '_name,' + userType + '_surname,' + userType + '_email,' + userType + '_password, user_type, register_date) VALUES (%s, %s, %s, %s, %s ,%s)'
            val = [(textName, textLName, textEmail, passwordHash,
                    userType,  datetime.now(pytz.utc))]
            cur.executemany(query, val)

            myconn.commit()

            # return to index form
            logger.warning('Successfully registered!')
            return redirect('/')
        else:
            flash('Email already registered, please log in!')
            logger.warning('Email already registered, please log in!')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/go_to_create_rating')
def go_to_create_rating():
    # get opposite user type
    if session['user_type'] == 'coach':
        opposite_user_type = 'coachee'
    else:
        opposite_user_type = 'coach'
    
    # create a connection
    myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
                'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))
    #create a cursor
    cursor = myconn.cursor() 
    #execute select statement to fetch data to be displayed in combo/dropdown
    cursor.execute('SELECT ' + opposite_user_type + '_email FROM ' + opposite_user_type) 
    #fetch all rows ans store as a set of tuples 
    emaillist = cursor.fetchall() 
    return render_template('rating.html', emaillist=emaillist)

@app.route('/go_to_view_ratings_recieved')
def go_to_view_ratings_recieved():
    '''Collecting the comments from the database and passing it to the html form'''
    # Initialise mysql
    myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
                'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

    cur = myconn.cursor()
    
    # Get their id from db
    their_id = None
    coach_rated = False
    if session['user_type'] == 'coach':
        # if they are a coach
        query = 'SELECT coach_id FROM coach WHERE coach_email = "' + session['email'] + '";'
        cur.execute(query)
        their_id = cur.fetchone()[0]
        # updating coach_rated boolean
        coach_rated = True
    else:
        # get their id
        query = 'SELECT coachee_id FROM coachee WHERE coachee_email = "' + session['email'] + '";'
        cur.execute(query)
        their_id = cur.fetchone()[0]
    
    #execute select statement to fetch data to be displayed in combo/dropdown
    cur.execute('SELECT rating_comment, star_rating FROM rating WHERE (' + session['user_type'] +'_id_fk = "' + str(their_id) + '") AND (coach_rated = '+str(coach_rated)+')') 
    #fetch all rows ans store as a set of tuples 
    commentlist = cur.fetchall() 

    '''Collecting the avg rating from the database and passing it to the html form'''
    # Get their avg from db
    avg_rating = None

    if session['user_type'] == 'coach':
        # if they are a coach
        query = 'SELECT coach_avg_rating FROM coach WHERE coach_email = "' + session['email'] + '";'
        cur.execute(query)
        avg_rating = cur.fetchone()[0]
    else:
        # get ratee id
        query = 'SELECT coachee_avg_rating FROM coachee WHERE coachee_email = "' + session['email'] + '";'
        cur.execute(query)
        avg_rating = cur.fetchone()[0]

    return render_template('view_rating_received.html', commentlist=commentlist, avg_rating=avg_rating)

@app.route('/go_to_view_ratings_given')
def go_to_view_ratings_given():
    '''Collecting the comments from the database and passing it to the html form'''
    # Initialise mysql
    myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
                'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

    cur = myconn.cursor()
    
    # Get their id from db
    their_id = None
    coach_rated = False
    if session['user_type'] == 'coach':
        # if they are a coach
        query = 'SELECT coach_id FROM coach WHERE coach_email = "' + session['email'] + '";'
        cur.execute(query)
        their_id = cur.fetchone()[0]
        # updating coach_rated boolean
        coach_rated = True
    else:
        # get their id
        query = 'SELECT coachee_id FROM coachee WHERE coachee_email = "' + session['email'] + '";'
        cur.execute(query)
        their_id = cur.fetchone()[0]
    
    #execute select statement to fetch data to be displayed in combo/dropdown
    cur.execute('SELECT rating_comment, star_rating FROM rating WHERE (' + session['user_type'] +'_id_fk = "' + str(their_id) + '") AND (coach_rated = '+str(not coach_rated)+')') 
    #fetch all rows ans store as a set of tuples 
    commentlist = cur.fetchall() 

    return render_template('view_rating_given.html', commentlist=commentlist)

# logic to create a rating
@app.route('/create_rating',methods=['GET','POST'])
def create_rating():
    rating = -1
    email = '-1'

    if request.method == 'POST':
        if 'rating' in request.form:
            content = int(request.form['rating'])
            rating = content

        if 'emailid' in request.form:
            content = request.form['emailid']
            email = content
        
        if 'comment' in request.form:
            content = request.form['comment']
            comment = content

        # Initialise mysql
        myconn = mysql.connector.connect(host=os.getenv('HOST'), user=os.getenv(
                    'USER'), passwd=os.getenv('PASSWD'), database=os.getenv('DATABASE'))

        cur = myconn.cursor()

        # declare coach rated boolean as True
        coach_rated = True

        # getting coachID or coacheeID for rater
        raterID = None
        if session['user_type'] == 'coach':
            # if rater is a coach
            query = 'SELECT coach_id FROM coach WHERE coach_email = "' + session['email'] + '";'
            cur.execute(query)
            raterID = cur.fetchone()[0]

            # get ratee id
            query = 'SELECT coachee_id FROM coachee WHERE coachee_email = "' + email + '";'
            cur.execute(query)
            rateeID = cur.fetchone()[0]

            # set coach_rated boolean to False
            coach_rated = False

        else:
            # if rater is a coachee
            query = 'SELECT coachee_id FROM coachee WHERE coachee_email = "' + session['email'] + '";'
            cur.execute(query)
            raterID = cur.fetchone()[0]

            # get ratee id
            query = 'SELECT coach_id FROM coach WHERE coach_email = "' + email + '";'
            cur.execute(query)
            rateeID = cur.fetchone()[0]

        # Populate table
        # A coach has been rated
        if coach_rated:
            try:
                    
                query = 'INSERT INTO rating (coach_id_fk, coachee_id_fk, star_rating, rating_comment, coach_rated, coachee_rated, register_date) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                val = [(rateeID, raterID, rating, comment, coach_rated, (not coach_rated),datetime.now(pytz.utc))]
                cur.executemany(query, val)

                myconn.commit()

                
            except:
                myconn.rollback()

            myconn.close()
            # A coachee has been rated
        else:
            try:
                    
                query = 'INSERT INTO rating (coach_id_fk, coachee_id_fk, star_rating, rating_comment, coach_rated, coachee_rated, register_date) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                val = [(raterID, rateeID, rating, comment, coach_rated, (not coach_rated),datetime.now(pytz.utc))]
                cur.executemany(query, val)

                myconn.commit()

                
            except:
                myconn.rollback()

            myconn.close()


        return redirect(url_for('success'))
    else:
        # Failed rating
        flash('Failed to create rating, pleae try again!')
        logger.warning('Failed to create rating, pleae try again!')
        return render_template('rating.html')

# logic to view received ratings
@app.route('/view_rating_received',methods=['GET','POST'])
def view_rating_received():
    if request.method == 'GET':
        pass

# generic Flask app guard
if __name__ == '__main__':
    app.run(debug=True)

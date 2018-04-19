from flask import Flask, request, jsonify, abort, g
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import pbkdf2_sha256
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


def hash_password(password):    # add it to the user class probably
    password = 'salt..&&0834' + password
    hash = pbkdf2_sha256.hash(password)
    return hash



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    roll_number = db.Column(db.String(20), unique=True)
    course = db.Column(db.String(20))
    branch = db.Column(db.String(20))
    id_card_url = db.Column(db.String(250))
    lib_card_url = db.Column(db.String(250))
    aadhar_card_url = db.Column(db.String(250))
    hostel_id_card_url = db.Column(db.String(250))

    def __init__(self, username, password, email):
        self.username = username
        self.password_hash = hash_password(password)
        self.email = email

    def verify_password(self, password):
        try:
            hash = hash_password(password)  # Doubt in this since password is hashed
            if hash == self.password_hash:
                return True
        
            return False
        except Exception as e:
            return False, "Exception occurred" #If error occurs then remove exception occurred.

    def __repr__(self):
        return '<User %r>' % self.username


class Notice(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    date_time = db.Column(db.DateTime, default=datetime.datetime.now())
    title = db.Column(db.String(250))
    content = db.Column(db.String(1000))
    branch = db.Column(Db.String(20))

    def __init__(self, title, content, branch):
        self.title = title
        self.content = content
        self.branch = branch
        




@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(hash_password(password)):
        return False
    # g is a thread local Ref - https://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    g.user = user
    return True



@app.route('/api/students/create_users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    hash = hash_password(password)

    email = request.json.get('email')
    if username is None or password is None:
        abort(400)
    if User.query.filter_by(username=username).first() is not None:
        abort(400)
    user = User(username=username, password_hash=hash, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'username': username,
        'status': 'success'
    })


@app.route('/api/students/update_profile', methods=['POST'])
@auth.login_required
def update_profile():
    user = g.user
    id_card_url = request.json.get('id_card_url')
    lib_card_url = request.json.get('lib_card_url')
    hostel_id_card_url = request.json.get('hostel_id_card_url')
    aadhar_card_url = request.json.get('aadhar_card_url')
    email = request.user.get('email')
    password = requeust.user.get('password')
    hash = hash_password(password)

    not_valid_url = valid_urls([id_card_url, lib_card_url, hostel_id_card_url, aadhar_card_url]) # TODO : write function using regex
    not_valid_email = valid_email(email) # TODO : write function using regex

    if not_valid_url == False and not_valid_email == False:
        try :
            user.id_card_url = id_card_url
            user.lib_card_url = lib_card_url
            user.hostel_id_card_url = hostel_id_card_url
            user.aadhar_card_url = aadhar_card_url
            user.email = email
            user.password_hash = hash
            db.session.commit()
        except Exception as e:
            abort(Response(jsonify({
                'content' : 'Unsuccessful in changing data'
            })))
    else 
        abort(Response(jsonify({
            'content' : 'Wrong information'
        })))


    ## check which data is received to update and update in db
    return jsonify({
        'content': '%s data changed successfully' % user.username
    })


@app.route('/', methods=['GET'])
@auth.login_required
def index():
    return jsonify({
        'name': '%s' % g.user.username,
        'api': 'College Management API',
        'type': 'Major Project'
    })


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter_by(username = username).first()
    if user is None:
        abort(400)
    if user.verify_password(password):
        return jsonify(
            {
                'username' : g.user.username
                'email' : g.user.email
                'roll_number' : g.user.roll_number
                'branch' : g.user.branch
                'course' : g.user.course
                'id_card_url' : g.user.id_card_url
                'lib_card_url' : g.user.lib_card_url
                'id' : g.user.id
            }
        )


# creating dummy user
db.create_all()

if __name__ == '__main__':
    app.run()

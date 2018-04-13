from flask import Flask, request, jsonify, abort, g
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


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
        self.password_hash = pwd_context.encrypt(password)
        self.email = email

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return '<User %r>' % self.username


@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    # g is a thread local Ref - https://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    g.user = user
    return True


@app.route('/api/students/create_users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    if username is None or password is None:
        abort(400)
    if User.query.filter_by(username=username).first() is not None:
        abort(400)
    user = User(username=username, password=password, email=email)
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


# creating dummy user
db.create_all()

if __name__ == '__main__':
    app.run()

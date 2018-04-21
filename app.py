from flask import Flask, request, jsonify, abort, g, Response
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
import os
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
        return 'User : ' + self.username + '\nemail : ' + self.email





class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.datetime.now())
    title = db.Column(db.String(250))
    content = db.Column(db.String(1000))
    branch = db.Column(db.String(20))

    def __init__(self, title, content, branch):
        self.title = title
        self.content = content
        self.branch = branch

    def __repr__(self):
        return "Title: "+self.title +"\nContent: "+self.content+"\n"


@app.route('/api/notice/create_notice', methods=['POST'])
@auth.login_required
def create_notice():
    try:
        title = request.json.get('title')
        branch = request.json.get('branch')
        content = request.json.get('content')

        if title is None or branch is None or content is None:
            return jsonify({
                'code' : 400,
                'content' : 'All the fields are required'
            })

        new_notice = Notice(title = title, content = content, branch = branch)
        try:
            db.session.add(new_notice)
            db.session.commit()
            return jsonify({
                'code':201,
                'content': 'Notice create successfully'
            })
        except Exception as e:
            return jsonify({
                'code': 503,
                'content' : 'Unable to create notice',
                'exception' : e.__str__()
            })

    except Exception as e:
        return jsonify({
            'code': 500,
            'content':'Something went wrong. Please try again',
            'exception': e.__str__()
        })


@app.route('/api/notice/view_notices', methods=['GET'])
@auth.login_required
def view_notices():
    try:
        branch = request.json.get('branch')
        if branch is None:
            return jsonify({
                'code':400,
                'content':'Branch is required'
            })
        try:
            notices = Notice.query.filter_by(branch=branch)
        except Exception as e:
            return jsonify({
                'code':503,
                'content':'Unable to access database',
                'exception' : e.__str__()
            })
        new_notices = [[]]
        sorted(notices, key=lambda notice: notice.id, reverse=True)

        for notice_ in notices:
            new_notice = [notice_.id, notice_.title, notice_.content, notice_.date_time]
            new_notices += [new_notice]

        return jsonify({
            'code': 201,
            'notices': new_notices
        })
    except Exception as e:
        return jsonify({
            'code':400,
            'content':'Bad request'
        })


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
    id_card_url = request.json.get('id_card_url')
    lib_card_url = request.json.get('lib_card_url')
    hostel_id_card_url = request.json.get('hostel_id_card_url')
    aadhar_card_url = request.json.get('aadhar_card_url')
    email = request.json.get('email')
    password = request.json.get('password')
    hash = pwd_context.encrypt(password)

    not_valid_url = valid_urls(
        [id_card_url, lib_card_url, hostel_id_card_url, aadhar_card_url])  # TODO : write function using regex
    not_valid_email = valid_email(email)  # TODO : write function using regex

    if not_valid_url == False and not_valid_email == False:
        try:
            user.id_card_url = id_card_url
            user.lib_card_url = lib_card_url
            user.hostel_id_card_url = hostel_id_card_url
            user.aadhar_card_url = aadhar_card_url
            user.email = email
            user.password_hash = hash
            db.session.commit()
        except Exception as e:
            abort(Response(jsonify({
                'content': 'Unsuccessful in changing data'
            })))
    else:
        abort(Response(jsonify({
            'content': 'Wrong information'
        })))

    ## check which data is received to update and update in db
    return jsonify({
        'content': '%s data changed successfully' % user.username
    })


def valid_email(email):
    # write logic
    return True


def valid_urls(email_list):
    # write logic
    return True


@app.route('/', methods=['GET'])
@auth.login_required
def index():
    return jsonify({
        'name': '%s' % g.user.username,
        'api': 'College Management API',
        'type': 'Major Project'
    })


@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    if g.user is None:
        abort(400)
    return jsonify(
        {
            'username': g.user.username,
            'email': g.user.email,
            'roll_number': g.user.roll_number,
            'branch': g.user.branch,
            'course': g.user.course,
            'id_card_url': g.user.id_card_url,
            'lib_card_url': g.user.lib_card_url,
            'id': g.user.id
        }
    )


# creating dummy user
db.create_all()

## sudo ufw disable  -> To disable firewall in ubuntu to access flask server from Mobile

if __name__ == '__main__':
    for user in User.query.all():
        print(user)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

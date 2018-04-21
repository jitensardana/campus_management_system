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
    __tablename__ = 'Users'
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
    user_access_level = db.Column(db.Integer) # 1 for student, 2 for working staff, 3 for teachers and admin departments, 4 for HOD, 5 rest

    def __init__(self, username, password, email, user_access_level=1):
        self.username = username
        self.password_hash = pwd_context.encrypt(password)
        self.email = email
        self.user_access_level = user_access_level

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return 'User : ' + self.username + '\nemail : ' + self.email


class Notice(db.Model):
    __tablename__ = "Notices"
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.datetime.now())
    title = db.Column(db.String(250))
    content = db.Column(db.String(1000))
    branch = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    date_modified = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, title, content, branch, user):
        self.title = title
        self.content = content
        self.branch = branch
        self.created_by = user.id

    def __repr__(self):
        return "Title: "+self.title +"\nContent: "+self.content+"\nCreated By: " + self.created_by+"\n"


@app.route('/api/notice/create_notice', methods=['POST'])
@auth.login_required
def create_notice():
    user_current = g.user
    if user_current.user_access_level >= 2 :
        try:
            title = request.json.get('title')
            branch = request.json.get('branch')
            content = request.json.get('content')

            if title is None or branch is None or content is None:
                return jsonify({
                    'code': 400,
                    'content': 'All the fields are required'
                })

            new_notice = Notice(title=title, content=content, branch=branch, user=user_current)
            try:
                db.session.add(new_notice)
                db.session.commit()
                # g.notice = new_notice  Don't know it's use yet
                return jsonify({
                    'code': 201,
                    'content': 'Notice create successfully'
                })
            except Exception as e:
                return jsonify({
                    'code': 503,
                    'content': 'Unable to create notice',
                    'exception': e.__str__()
                })

        except Exception as e:
            return jsonify({
                'code': 500,
                'content': 'Something went wrong. Please try again',
                'exception': e.__str__()
            })
    else:
        return jsonify({
            'code':400,
            'content':'Permission denied'
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


@app.route('/api/notice/update_notice', methods=['POST'])
@auth.login_required
def update_notice():
    try:
        user_current = g.user
        if user_current.user_access_level >= 2:
            notice_id = request.json.get('id')
            title = request.json.get('title')
            content = request.json.get('content')

            if id is None or title is None or content is None:
                return jsonify({
                    'code': 403,
                    'content': 'Request contains empty fields',

                })

            try:
                notice = Notice.query.filter_by(id=notice_id).first()
                notice.title = title
                notice.content = content
                notice.date_modified = datetime.datetime.now()
                if notice.created_by != user_current.id:
                    return jsonify({
                        'code': 400,
                        'content': 'You have not created this notice'
                    })
                try:
                    db.session.commit()
                    return jsonify({
                        'code': 201,
                        'content': 'Changes made successfully'
                    })
                except Exception as e:
                    return jsonify({
                        'code':503,
                        'content' : 'Unable to change'
                    })
            except Exception as e:
                return jsonify({
                    'code': 503,
                    'content': 'Unable to access database',
                    'exception': e.__str__()
                })
        else:
            return jsonify({
                'code':400,
                'content': 'Permission denied'
            })
    except Exception as e:
        return jsonify({
            'code':400,
            'content' : 'Error occurred',
            'exception': e.__str__()
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
    user_access_level = request.json.get('user_access_level')

    if username is None or password is None or user_access_level > 5 or user_access_level < 1:
        abort(400)
    if User.query.filter_by(username=username).first() is not None:
        g.user = User.query.filter_by(username=username).first()
        return

    user = User(username=username, password=password, email=email, user_access_level=user_access_level)
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

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
    user_access_level = db.Column(db.Integer)
    notices = db.relationship("Notice", backref="Users")
    requests = db.relationship("ApplicationRequests", backref="Users")

    # 1 for student, 2 for COE department, 3 for admin, 4 for branch department, 5 HOD

    def __init__(self, username, password, email, user_access_level=1):
        self.username = username
        self.password_hash = pwd_context.encrypt(password)
        self.email = email
        if user_access_level > 5 or user_access_level < 1:
            user_access_level = 1
        self.user_access_level = user_access_level

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def get_json(self):
        return {
            'username': self.username,
            'email': self.email,
            'roll_number': self.roll_number,
            'branch': self.branch,
            'course': self.course,
            'user_access_level': self.user_access_level,
            'id_card_url': self.id_card_url,
            'lib_card_url': self.lib_card_url,
            'id': self.id
        }

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
    attachment_url = db.Column(db.String(250))

    def __init__(self, title, content, branch, user):
        self.title = title
        self.content = content
        self.branch = branch
        self.created_by = user.id

    def __repr__(self):
        return "Title: " + self.title + "\nContent: " + self.content + "\nCreated By: " + str(self.created_by) + "\n"

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class ApplicationRequests(db.Model):
    __tablename__ = "Requests"
    id = db.Column(db.Integer, primary_key=True)
    request_from = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    request_type = db.Column(db.Integer, nullable=False)
    time_created = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    time_modified = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    time_completed = db.Column(db.DateTime)
    state = db.Column(db.Integer, default=0) # 0: Received, 1:Read, 3: Processing 4: Rejected, 5:Completed
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000))
    access_level = db.Column(db.Integer, nullable=False)
    attachment_url = db.Column(db.String(250))

    def __init__(self, request_from, request_type, title, content):
        self.request_from = request_from
        self.request_type = request_type
        if request_type == 4: #Department request
            self.access_level = 4
        elif request_type == 2: #coe
            self.access_level = 2
        elif request_type == 3 : #admin
            self.access_level = 3
        else:
            self.access_level = 4

        self.title = title
        self.content = content


    def __repr__(self):
        return "Request id: "+self.request_id+"\nTitle: "+self.title+"\nRequest from: "+self.request_from+"\nRequest type: "+self.request_type+"\n"


@app.route('/api/requests/create_request', methods=['POST'])
@auth.login_required
def create_request():
    try:
        curr_user = g.user
        title = request.json.get('title')
        content = request.json.get('content')
        request_type = request.json.get('request_type')
        request_from = curr_user.id

        if title is None or request_type is None or request_from is None:
            return jsonify({
                'code':400,
                'content': 'Bad Request',
                'exception': 'Data is null'
            })
        try:
            new_request = ApplicationRequests(request_from, request_type, title, content)
            try:
                db.session.add(new_request)
                db.session.commit()
                return jsonify({
                    'code':200,
                    'content': 'Request created successfully'
                })
            except Exception as e:
                return jsonify({
                    'code':503,
                    'content': 'Internal server error',
                    'exception': e.__str__()
                })

        except Exception as e:
            return jsonify({
                'code':400,
                'content':'Unable to create request',
                'exception': e.__str__()
            })


    except Exception as e:
        return jsonify({
            'code':400,
            'content': 'Bad Request',
            'exception': e.__str__()
        })


@app.route('/api/requests/view_request', methods=['POST'])
@auth.login_required
def view_request():
    try:
        curr_user = g.user
        if curr_user.user_access_level > 1 and curr_user.user_access_level < 5:
            access_level = curr_user.user_access_level
            try:
                requests = ApplicationRequests.query.filter_by(access_level=access_level)
                new_requests = []

                for request_ in requests:
                    new_request = {
                        'id' : request_.id,
                        'type': request_.request_type,
                        'title': request_.title,
                        'content': request_.content,
                        'state': request_.state,
                        'time_modified': request_.time_modified,
                        'reqeust_from' : User.query.filter_by(id=request_.request_from).first().get_json()
                    }
                    new_requests.append(new_request)

                sorted(new_requests, key=lambda new_request: new_request['time_modified'], reverse=True)

                return jsonify({
                    'code': 200,
                    'requests': new_requests
                })
            except Exception as e:
                return jsonify({
                    'code':400,
                    'content': 'Unable to fetch requests',
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
            'content': 'Unable to view requests',
            'exception': e.__str__()
        })


@app.route('/api/requests/update_requests', methods=['POST'])
@auth.login_required
def update_request():
    curr_user = g.user
    try:
        request_id = request.json.get('id')
        request_title = request.json.get('title')
        request_content = request.json.get('content')
        request_type = request.json.get('type')

        if request_id is None or request_title is None or request_content is None or request_type is None:
            return jsonify({
                'code':400,
                'content': 'Some fields are empty'
            })

        try:
            curr_request = ApplicationRequests.query.filter_by(id=request_id)
            if curr_request.request_from == curr_user.id:
                try:
                    curr_request.title = request_title
                    curr_request.content = request_content
                    curr_request.request_type = request_type
                    curr_request.time_modified = datetime.datetime.now()
                    db.session.commit()
                    return jsonify({
                        'code':200,
                        'content': 'Changes made successfully'
                    })
                except Exception as e:
                    return jsonify({
                        'code': 400,
                        'content': 'Unable to make changes'
                    })

        except Exception as e:
            return jsonify({
                'code': 400,
                'content': 'Unable to access database'
            })

        else:
            return jsonify({
                'code': 400,
                'content': 'Permission Denied'
            })

    except Exception as e:
        return jsonify({
            'code':400,
            'content': 'Bad Request'
        })


@app.route('/api/notice/create_notice', methods=['POST'])
@auth.login_required
def create_notice():
    user_current = g.user
    if user_current.user_access_level >= 2:
        try:
            title = request.json.get('title')
            branch = request.json.get('branch')
            content = request.json.get('content')

            print(title)
            print(branch)
            print(content)

            if title is None or branch is None or content is None:
                return jsonify({
                    'code': 400,
                    'content': 'All the fields are required'
                })

            new_notice = Notice(title=title, content=content, branch=branch, user=user_current)
            try:
                db.session.add(new_notice)
                db.session.commit()
                print("Notice created successfully")
                # g.notice = new_notice  Don't know it's use yet
                return jsonify({
                    'code': 201,
                    'content': 'Notice created successfully'
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
            'code': 400,
            'content': 'Permission denied'
        })


@app.route('/api/notice/view_notices', methods=['GET'])
@auth.login_required
def view_notices():
    try:
        branch = request.json.get('branch')
        if branch is None:
            return jsonify({
                'code': 400,
                'content': 'Branch is required'
            })
        try:
            notices = Notice.query.filter_by(branch=branch)
        except Exception as e:
            return jsonify({
                'code': 503,
                'content': 'Unable to access database',
                'exception': e.__str__()
            })
        new_notices = []

        for notice_ in notices:
            new_notice = {
                'id': notice_.id,
                'title': notice_.title,
                'content': notice_.content,
                'branch': notice_.branch,
                'attachment_url': notice_.attachment_url,
                'date_time': notice_.date_time
            }
            # new_notice = [notice_.id, notice_.title, notice_.content, notice_.date_time]
            new_notices.append(new_notice)

        sorted(new_notices, key=lambda new_notice: new_notice['date_time'], reverse=True)

        return jsonify({
            'code': 201,
            'notices': new_notices
        })
    except Exception as e:
        return jsonify({
            'code': 400,
            'content': 'Bad request'
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
                notice.date_modified = datetime.datetime.now()
                if notice.created_by != user_current.id:
                    return jsonify({
                        'code': 400,
                        'content': 'You have not created this notice'
                    })
                notice.title = title
                notice.content = content
                try:
                    db.session.commit()
                    return jsonify({
                        'code': 201,
                        'content': 'Changes made successfully'
                    })
                except Exception as e:
                    return jsonify({
                        'code': 503,
                        'content': 'Unable to change'
                    })
            except Exception as e:
                return jsonify({
                    'code': 503,
                    'content': 'Unable to access database',
                    'exception': e.__str__()
                })
        else:
            return jsonify({
                'code': 400,
                'content': 'Permission denied'
            })
    except Exception as e:
        return jsonify({
            'code': 400,
            'content': 'Error occurred',
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
    user_access_level = int(request.json.get('user_access_level'))
    branch = request.json.get('branch')

    if username is None or password is None or user_access_level > 5 or user_access_level < 1:
        abort(400)
    if User.query.filter_by(username=username).first() is not None:
        g.user = User.query.filter_by(username=username).first()
        return

    user = User(username=username, password=password, email=email, user_access_level=user_access_level)
    if branch is not None:
        user.branch = branch
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
    return jsonify(g.user.get_json())


# creating dummy user
db.create_all()

## sudo ufw disable  -> To disable firewall in ubuntu to access flask server from Mobile

if __name__ == '__main__':
    for user in User.query.all():
        print(user)
    for notice in Notice.query.all():
        print(notice)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


"""
curl -i -X POST -H "Content-Type: application/json" -d '{"username":"vivek","password":"vivek","email":"vivek","user_access_level":"1"}' http://0.0.0.0:5000/api/students/create_users


curl -i -X POST -H "Content-Type: application/json" -d '{"username":"jiten","password":"jiten803","email":"jitensardana@gmail.com","branch":"ece","user_access_level":"4"}' http://0.0.0.0:5000/api/students/create_users


view notices : curl -u miguel:python -i -X GET -H "Content-Type: application/json" -d '{"branch":"EC"}' http://0.0.0.0:5000/api/notice/view_notices

create notice : curl -u jiten:jiten803 -i -X POST -H "Content-Type: application/json" -d '{"title":"third", "content":"third", "branch":"EC"}' http://0.0.0.0:5000/api/notice/create_notice



create request : curl -u jiten:jiten803 -i -X POST -H "Content-Type: application/json" -d '{"title":"First", "content":"Request", "request_type":4}' http://0.0.0.0:5000/api/requests/create_request


view request : curl -u jiten:jiten803 -i -X POST -H "Content-Type: application/json" -d '{}' http://0.0.0.0:5000/api/requests/view_request

"""
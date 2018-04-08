import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import flask_login
from werkzeug.utils import secure_filename
from PyPDF2 import PdfFileReader, PdfFileWriter

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

logged_in = False

app = Flask(__name__, static_url_path="/static")
app.secret_key = "some_secret_key"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# limit upload size upto 8mb
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

temp_users = {'admin': 'password'}


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    if username not in temp_users:
        return

    user = User()
    user.id = username
    return user


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/dashboard/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/login/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        if flask_login.current_user.is_authenticated:
            return render_template('dashboard.html')
        return render_template("login.html")

    error = ''
    try:
        if request.method == "POST":
            attempted_username = request.form['username']
            attempted_password = request.form['password']

            if attempted_username in temp_users and temp_users[attempted_username] == attempted_password:
                user = User()
                user.id = attempted_username
                flask_login.login_user(user)
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid username or password. Try Again"

        return render_template('login.html', error=error)

    except Exception as e:
        print('exception occured')
        return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

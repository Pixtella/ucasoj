from flask import Flask
from flask import render_template
from flask import request

import datetime

from contests import Contest,upcomingContestsInfo,contestHistoryInfo

commonArgs = {}
def refreshCommonArgs():
    commonArgs["year"] = datetime.datetime.now().year

app = Flask(__name__)

# @app.route("/")
# def hello_world():
#     return "<h1>Hello, World!</h1>"


@app.route('/', methods=['GET', 'POST'])
def home():
    refreshCommonArgs()
    args = commonArgs.copy()
    return render_template("home.html", **args)
    # return '<h1>Home</h1>'

@app.route('/contests', methods=['GET', 'POST'])
def contests():
    refreshCommonArgs()
    args = commonArgs.copy()
    
    args["upcomingContests"] = upcomingContestsInfo()
    args["historicContests"] = contestHistoryInfo()

    return render_template("contests.html", **args)


@app.route('/signin', methods=['GET'])
def signin_form():
    return '''<form action="/signin" method="post">
              <p><input name="username"></p>
              <p><input name="password" type="password"></p>
              <p><input type="file">Choose a file</p>
              <p><button type="submit">Sign In</button></p>
              </form>'''

@app.route('/signin', methods=['POST'])
def signin():
    # 需要从request对象读取表单内容：
    if request.form['username']=='admin' and request.form['password']=='password':
        return '<h3>Hello, admin!</h3>'
    return '<h3>Bad username or password.</h3>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("loginpage.html")
if __name__ == '__main__':
    app.run()

    "".format()
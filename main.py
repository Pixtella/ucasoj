from flask import Flask
from flask import render_template,redirect,url_for
from flask import request
import json
import requests
import hashlib
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


import datetime

from contest import *
from database import *

commonArgs = {}
judgerToken = "41d62e8a28dd18d8b80a77f9a3d0218ff67b7d91f0d5398781fffc0f7bf16e33"
submissionHeader = {"X-Judge-Server-Token": judgerToken, "Content-Type": "application/json"}

def refreshCommonArgs():
    commonArgs["year"] = datetime.datetime.now().year
    if current_user.is_authenticated:
        commonArgs["loginStatus"] = "Login Success"
        commonArgs["currentUser"] = current_user
    else:
        commonArgs["loginStatus"] = "Not Login"

app = Flask(__name__)
app.app_context().push()
app.secret_key = 'ucasoj_sec_key'
login_manager = LoginManager()
login_manager.init_app(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.root_path + '\ojdata.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + app.root_path + '/ojdata.db'
db = SQLAlchemy(app)
# @app.route("/")
# def hello_world():
#     return "<h1>Hello, World!</h1>"
resultLookUp = {0: "AC", -1: "WA", 1: "TLE", 2: "TLE", 3: "MLE", 4: "RE", 5:"SE"}






class dbProblem(db.Model):
    __tablename__ = 't_problem' # table name
    id = db.Column(db.Integer, primary_key=True) # problem id
    name = db.Column(db.String(80), nullable=False) # problem name
    timeLimit = db.Column(db.Integer, nullable=False) # in ms
    memoryLimit = db.Column(db.Integer, nullable=False) # in MB
    solved = db.Column(db.Integer, default=0) # number of accepted submissions
    submitted = db.Column(db.Integer, default=0) # number of submissions
    pdfpath = db.Column(db.String(256), nullable=False) # pdf path
    datapath = db.Column(db.String(256), nullable=False) # data path
    judgerid = db.Column(db.String(64), nullable=False) # judger id

class dbContestProblem(db.Model):
    id = db.Column(db.Integer, primary_key=True) # problem id
    idx = db.Column(db.String(80), nullable=False) # problem index
    solved = db.Column(db.Integer, default=0) # number of accepted submissions
    submitted = db.Column(db.Integer, default=0) # number of submissions

class dbContest(db.Model):
    __tablename__ = 't_contest' # table name    
    id = db.Column(db.Integer, primary_key=True) # contest id
    name = db.Column(db.String(80), nullable=False) # contest name
    start = db.Column(db.DateTime, nullable=False) # contest start time
    length = db.Column(db.Integer, nullable=False) # contest length in minutes
    problems = db.Column(db.String(1024), nullable=False) # problem list a dictionary mapping idx to id
    participants = db.Column(db.String(16384), nullable=False) # participant list
    # rank = db.Column(db.String(80), nullable=False) # rank list
    # ranktime = db.Column(db.DateTime, nullable=False) # rank update time
    # ranksealtime = db.Column(db.DateTime, nullable=False) # rank seal time

    def idx(self, problemid):
        ps = self.problemids()
        for i,pid in enumerate(ps):
            if pid == problemid:
                return chr(ord('A') + i)
        return '#'
    
    def problemids(self):
        return sorted(list(eval(self.problems).values()))
    
    def probname(self, problemid):
        return retrieveProblem(problemid).name

    def numberofAccepted(self, probid) -> int:
        
        return len(dbSubmission.query.filter_by(contest=self.id, problemid=probid, result="AC").all())

    def numberofAttempts(self, probid) -> int:

        return len(dbSubmission.query.filter_by(contest=self.id, problemid=probid).all())

    def isFirstBlood(self, userid, problemid):
        """
        Return whether a user is the first to solve a problem.
        """
        submissions = dbSubmission.query.filter_by(contest=self.id, problemid=problemid, result="AC").order_by(dbSubmission.submissiontime).all()
        if len(submissions) == 0:
            return False
        if submissions[0].userid == userid:
            return True
        return False

    def ranklist(self):
        """
        Return a list of rank.
        """
        ret = [[pla, retrieveUser(pla).name, self.solved(pla), self.penalty(pla)] for pla in eval(self.participants)]
        ret.sort(key=lambda x: (-x[2], x[3]))
        return ret
    
    def singlePenalty(self, userid, problemid):
        """
        Penalty of a user on a problem.
        """
        submissions = dbSubmission.query.filter_by(contest=self.id, userid=userid, problemid=problemid).all()
        penalty = 0
        ACed = False
        for s in submissions:
            if s.result == "AC":
                ACed = True
                penalty += int((s.submissiontime - self.start).total_seconds()) // 60 + 1
            else:
                penalty += 20
        if not ACed:
            penalty = 0
        return penalty

    def penalty(self, userid):
        """
        Penalty of a user.
        """
        penalty = 0
        for pid in self.problemids():
            penalty += self.singlePenalty(userid, pid)
        return penalty

    def solved(self, userid):
        """
        Number of problems solved a user.
        """
        submissions = dbSubmission.query.filter_by(contest=self.id, userid=userid, result="AC").all()
        solved = set()
        for s in submissions:
            solved.add(s.problemid)
        return len(solved)

    def status(self, userid, problemid):
        total = len(dbSubmission.query.filter_by(contest=self.id, userid=userid, problemid=problemid).all())
        firstac = dbSubmission.query.filter_by(contest=self.id, problemid=problemid, userid=userid, result="AC").order_by(dbSubmission.submissiontime).first()
        attempted = total > 0
        if firstac:
            return f"+ {total}/{self.singlePenalty(userid, problemid)}"
        elif attempted:
            return f"- {total}/{self.singlePenalty(userid, problemid)}"
        return "."
        return "+ 1/1" # '+': Accepted  '-': Rejected    attempts/penalty


class dbUser(db.Model, UserMixin):
    __tablename__ = 't_user' # table name
    id = db.Column(db.Integer, primary_key=True) # user id
    name = db.Column(db.String(64), nullable=False) # real name
    password = db.Column(db.String(64), nullable=False) # password hash
    # solved = db.Column(db.Integer, default=0) # number of problems solved
    # submitted = db.Column(db.Integer, default=0) # number of problems submitted
    # problmestatus=db.Column(db.String(20), default="") # problem status, W for wrong, A for solved, R for running, C for compileerror, blank for not submitted
    # penalty = db.Column(db.Integer, default=0) # total penalty time

class dbSubmission(db.Model):
    __tablename__ = 't_submission' # table name
    runid = db.Column(db.Integer, primary_key=True) # submission id
    userid = db.Column(db.Integer, nullable=False) # user id
    problemid = db.Column(db.Integer, nullable=False) # problem id
    submissiontime = db.Column(db.DateTime, nullable=False) # submission time
    compiler = db.Column(db.Integer, nullable=False) # compiler choice
    code = db.Column(db.String(10000), nullable=False) # code
    result = db.Column(db.String(64), default=0) # result
    compilemsg = db.Column(db.String(10000), default="") # compile message
    time = db.Column(db.Integer, default=0) # in ms
    memory = db.Column(db.Float, default=0) # in MB
    contest = db.Column(db.Integer, nullable=True) # contest id if it is a contest submission

#db.drop_all()
# db.create_all()

#db.session.add(Problem(id=1, name='A+B', time=1000, memory=256, pdfpath='A.pdf', datapath='A'))

def upcomingContestsInfo():
    """
    Return a list of upcoming contests.
    """
    curtime = datetime.datetime.now()
    allContests = dbContest.query.order_by(dbContest.start)
    upcomingContests = []
    for c in allContests:
        if c.start > curtime:
            # c.participants = eval(c.participants)
            upcomingContests.append(c)
    return upcomingContests
    # return [Contest()]

def contestHistoryInfo():
    """
    Return a list of historic contests.
    """
    curtime = datetime.datetime.now()
    allContests = dbContest.query.order_by(dbContest.start.desc())
    historicContests = []
    for c in allContests:
        if c.start < curtime:
            # c.participants = eval(c.participants)
            historicContests.append(c)
    return historicContests
    # return [Contest()]



def retrieveContest(contestid):
    """
    Find a contest by id.
    """
    return dbContest.query.filter_by(id=contestid).first()

    return testContest

def retrieveProblem(problemid):
    """
    Find a problem by id.
    """
    return dbProblem.query.filter_by(id=problemid).first()
    return testContestProblem


def retrieveContestProblem(contestid, problemindex):
    """
    Find a contest problem by contestid and problem index
    """
    dic = eval(dbContest.query.filter_by(id=contestid).first().problems)
    problemid = dic[problemindex]
    return retrieveProblem(problemid)
    return testContestProblem

def retrieveUser(userid):
    """
    Find a user by id.
    """
    return dbUser.query.filter_by(id=userid).first()

def retrieveSubmission(submissionid):
    """
    Find a submission by absolute identity
    """
    return dbSubmission.query.filter_by(runid=submissionid).first()
    # return testSubmission


@app.route('/', methods=['GET', 'POST'])
def home():
    refreshCommonArgs()
    args = commonArgs.copy()
    if current_user.is_authenticated:
        args["loginStatus"] = "Login Success"
        args["currentUser"] = current_user
    else:
        args["loginStatus"] = "Not Login"
    return render_template("home.html", **args)
    # return '<h1>Home</h1>'

@app.route('/contests', methods=['GET', 'POST'])
def contests():
    refreshCommonArgs()
    args = commonArgs.copy()
    
    args["upcomingContests"] = upcomingContestsInfo()
    args["historicContests"] = contestHistoryInfo()

    return render_template("contests.html", **args)

@app.route('/contest/<contestid>')
def contest(contestid):
    refreshCommonArgs()
    args = commonArgs.copy()
    curcontest = retrieveContest(contestid)

    args["contest"] = curcontest

    return render_template("contest.html", **args)

@app.route('/contest/<contestid>/<problemindex>', methods=['GET'])
def contestProblem(contestid, problemindex):
    refreshCommonArgs()
    args = commonArgs.copy()

    args["problem"] = retrieveContestProblem(contestid, problemindex)
    args["status"] = "View Problem"
    args["problemidx"] = problemindex

    return render_template("problem.html", **args)


def deliverJudgeRequest(userid, compiler, solcode, prob, contestid):
    body = {}
    language_config = {}
    if compiler == "cpp":
        compile = {"src_name": "main.cpp",
	            "exe_name": "main",
	            "max_cpu_time": 3000,
	            "max_real_time": 5000,
	            "max_memory": 128 * 1024 * 1024,
	            "compile_command": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_path} -lm -o {exe_path}"}
        run = {"command": "{exe_path}",
	            "seccomp_rule": "c_cpp",
	            "env": ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]}
        body["max_cpu_time"] = prob.timeLimit
        body["max_memory"] = prob.memoryLimit * 1024 * 1024

    elif compiler == "java":
        compile = {"src_name": "Main.java",
                "exe_name": "Main",
                "max_cpu_time": 3000,
                "max_real_time": 5000,
                "max_memory": -1,
                "compile_command": "/usr/bin/javac {src_path} -d {exe_dir} -encoding UTF8"}
        run = {"command": "/usr/bin/java -cp {exe_dir} -Xss1M -XX:MaxPermSize=16M -XX:PermSize=8M -XX:CompileThreshold=10 -XX:+UseSerialGC -Xms16M -Xmx{max_memory}K -Djava.security.manager -Djava.security.policy==/etc/java_policy -Djava.awt.headless=true Main",
                "seccomp_rule": None,
                "env": ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"],
                "memory_limit_check_only": 1}
        body["max_cpu_time"] = prob.timeLimit * 2
        body["max_memory"] = prob.memoryLimit * 1024 * 1024 * 2

    elif compiler == "py3":
        compile = {"src_name": "solution.py",
                "exe_name": "__pycache__/solution.cpython-36.pyc",
                "max_cpu_time": 3000,
                "max_real_time": 5000,
                "max_memory": 128 * 1024 * 1024,
                "compile_command": "/usr/bin/python3 -m py_compile {src_path}"}
        run = {"command": "/usr/bin/python3 {exe_path}",
                "seccomp_rule": "general",
                "env": ["PYTHONIOENCODING=UTF-8", "LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]}
        body["max_cpu_time"] = prob.timeLimit * 2
        body["max_memory"] = prob.memoryLimit * 1024 * 1024 * 2

    elif compiler == "c":

        compile = {"src_name": "main.c",
                "exe_name": "main",
                "max_cpu_time": 3000,
                "max_real_time": 5000,
                "max_memory": 128 * 1024 * 1024,
                "compile_command": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c99 {src_path} -lm -o {exe_path}"}
        run = {"command": "{exe_path}",
                "seccomp_rule": "c_cpp",
                "env": ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]}
        body["max_cpu_time"] = prob.timeLimit
        body["max_memory"] = prob.memoryLimit * 1024 * 1024



    language_config["compile"] = compile
    language_config["run"] = run
    body["src"] = solcode.read().decode('utf-8')
    body["language_config"] = language_config
    body["test_case_id"] = prob.judgerid
    body["output"] = True

    res = requests.post("http://0.0.0.0:8080/judge", json=body, headers=submissionHeader)
    
    res = str(res.content, 'UTF-8')
    res = json.loads(res)
    data = res["data"]
    res = [c["result"] for c in data]

    submission = None
    max_memory = max([c["memory"] for c in data])
    max_time = max([c["cpu_time"] for c in data])
    runid = dbSubmission.query.count() + 1
    for i,r in enumerate(res):
        if r != 0:
            submission = dbSubmission(runid=runid, userid=userid, problemid=prob.id, submissiontime=datetime.datetime.now(), compiler=compiler, code=body["src"], result=resultLookUp[r], compilemsg="123", time=max_time, memory=max_memory, contest=contestid)
            break
    for i,r in enumerate(res):
        print("cpu_time" + f"{data[i]['cpu_time']}")
    if not submission:
        submission = dbSubmission(runid=runid, userid=userid, problemid=prob.id, submissiontime=datetime.datetime.now(), compiler=compiler, code=body["src"], result=resultLookUp[0], compilemsg="123", time=max_time, memory=max_memory, contest=contestid)
    db.session.add(submission)
    db.session.commit()

@app.route('/contest/<contestid>/<problemindex>', methods=['POST'])
def contestProblemSubmit(contestid, problemindex):
    refreshCommonArgs()
    args = commonArgs.copy()

    prob = retrieveContestProblem(contestid, problemindex)
    args["problem"] = prob

    compiler = request.form["compiler"]
    solcode = request.files['solcode']
    
    if not solcode or not compiler or current_user.is_anonymous:
        args["status"] = "Submission Failed"
    else:
        args["status"] = "Submitted"
    
    deliverJudgeRequest(current_user.id, compiler, solcode, prob, contestid)


    return render_template("problem.html", **args)

@app.route('/submissions/<submissionid>')
def submissionView(submissionid):
    refreshCommonArgs()
    args = commonArgs.copy()

    args["submission"] = retrieveSubmission(submissionid)

    return render_template("submission.html", **args)

@login_manager.user_loader
def load_user(user_id):
    usr = dbUser.query.get(int(user_id))
    if usr:
        return usr
    return None

@app.route('/login', methods=['GET'])
def loginPage():
    refreshCommonArgs()
    args = commonArgs.copy()

    return render_template("loginpage.html", **args)

@app.route('/login', methods=['POST'])
def login():
    refreshCommonArgs()
    args = commonArgs.copy()

    username = request.form["usrn"]
    password = request.form["pasw"]
    usr = dbUser.query.filter_by(name=username).first()
    md = hashlib.md5(password.encode('utf-8')).hexdigest()
    if not usr or md != usr.password:
        return render_template("loginpage.html", **args)
    login_user(usr)
    args["loginStatus"] = "Login Success"
    args["currentUser"] = usr
    return render_template("home.html", **args)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     return render_template("loginpage.html")

@app.route('/test', methods=['GET'])
def test():
    # tc = dbContest(id=6, name="test", start=datetime.datetime.now(), length=120, problems="{'A':123,'B':456}")
    # db.session.add(tc)
    # db.session.commit()
    # cl = dbContest.query.all()
    # print(cl)
    tests = upcomingContestsInfo()
    tests[0].TestFunc()
    return "test"
    # return render_template("test.html")

def testinit():
    testProblem = dbProblem(id=1, name='A+B', timeLimit=1000, memoryLimit=256, pdfpath='./static/problems/1.pdf', datapath='./static/data/1', judgerid="32f6204a27f255bd70bea65f496a1074")
    testContest = dbContest(id=1, name="Round -1", start=datetime.datetime(2000, 1, 1, 9), length=300, problems="{'A':1,'B':2}", participants="[1,2]")
    md = hashlib.md5("123456".encode('utf-8'))
    testUser = dbUser(id=1, name="admin", password=md.hexdigest())

    db.session.add(testProblem)
    db.session.add(testContest)
    db.session.add(testUser)
    db.session.commit()

    testContest2 = dbContest(id=2, name="Round 1", start=datetime.datetime(2023, 7, 1, 9), length=300, problems="{'A':1,'B':2,'C':3,'D': 4, 'E':5}", participants="[1,2]")
    db.session.add(testContest2)
    db.session.commit()

    testProblem2 = dbProblem(id=2, name="A+B Plus", timeLimit=1000, memoryLimit=256, pdfpath="1234", datapath="123", judgerid="8ecfd953308f2ac508727b350cd39a3c")
    db.session.add(testProblem2)
    db.session.commit()

    testSubmission = dbSubmission(runid=1, userid=1, problemid=1, submissiontime=datetime.datetime.now(), compiler=0, code="123", result="AC", compilemsg="123", time=10, memory=25, contest=1)
    db.session.add(testSubmission)
    db.session.commit()
    testSubmission2 = dbSubmission(runid=2, userid=1, problemid=1, submissiontime=datetime.datetime.now(), compiler=0, code="123", result="WA", compilemsg="123", time=10, memory=25, contest=1)
    db.session.add(testSubmission2)
    db.session.commit()

    testProblem3 = dbProblem(id=3, name="COF", timeLimit=3000, memoryLimit=256, pdfpath="1234", datapath="123", judgerid="740e5b8ab0cb5c64fa803fa4d8eb6cbc")
    db.session.add(testProblem3)
    db.session.commit()

    testProblem4 = dbProblem(id=4, name="Polygon", timeLimit=8000, memoryLimit=512, pdfpath="1234", datapath="123", judgerid="e7c9dccb39c45874267b214dbfc9db59")
    db.session.add(testProblem4)
    db.session.commit()

    testProblem5 = dbProblem(id=5, name="CDQ", timeLimit=8000, memoryLimit=256, pdfpath="1234", datapath="123", judgerid="d3f1e57df35a0a498fcc3fe8eaf7d2fc")
    db.session.add(testProblem5)
    db.session.commit()

    md = hashlib.md5("456789".encode('utf-8'))
    testUser2 = dbUser(id=2, name="user", password=md.hexdigest())
    db.session.add(testUser2)
    db.session.commit()
    pass


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    testinit()
    app.run()

    "".format()




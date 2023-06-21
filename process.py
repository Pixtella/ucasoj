import threading
from enum import Enum
from datetime import datetime,timedelta

from database import *
from judge import addjudge

problemcount=13	# 题目数量
conteststarttime=datetime(2020,1,1,0,0,0)	# 开始时间
contestsealtime=datetime(2020,1,1,0,0,0)	# 封榜时间
contestendtime=datetime(2020,1,1,0,0,0)	# 结束时间

class SubmissionResult(Enum):
	DEFAULT=0
	COMPILING=1
	COMPILEERROR=2
	RUNNING=3
	ACCEPTED=4
	WRONGANSWER=5
	TIMELIMITEXCEED=6
	MEMORYLIMITEXCEED=7
	RUNTIMEERROR=8
	OUTPUTLIMIT=9
	UNKNOWNERROR=10

# Compile Choices
class Compiler(Enum):
	TEXT=0
	C=1
	CPP=2
	GO=3
	PYTHON=4

def submit(userid:int,problemid:int,code:str,compiler:Compiler):
	submissiontime=datetime.now()
	# TODO:generate runid
	runid=userid*1000000+userid.submitted
	# add to database
	submission=dbSubmission(runid,userid,problemid,compiler=compiler,code=code,submissiontime=submissiontime)
	user=dbUser.query.get(userid)
	user.submitted+=1
	problem=dbProblem.query.get(problemid)
	problem.submitted+=1
	submission.result=SubmissionResult.COMPILING
	db.session.add(submission)
	db.session.commit()
	# add to judge
	addjudge(runid,problemid,compiler,code)

def updatecompile(runid:int,compilesucceed:bool,compilemsg:str):
	submission=dbSubmission.query.get(runid)
	user = dbUser.query.get(submission.user)
	if compilesucceed:
		submission.result=SubmissionResult.RUNNING
		if user.problmestatus[submission.problem]!='A':
			user.problmestatus[submission.problem]='R'
	else:
		submission.result=SubmissionResult.COMPILEERROR
		if user.problmestatus[submission.problem]!='A':
			user.problmestatus[submission.problem]='C'
	submission.compilemsg=compilemsg
	db.session.commit()

def updatejudge(runid:int,result:SubmissionResult,time:int,memory:int):
	submission=dbSubmission.query.get(runid)
	user=dbUser.query.get(submission.user)
	problem=dbProblem.query.get(submission.problem)
	submission.result=result.value
	submission.time=time
	submission.memory=memory
	if user.problmestatus[submission.problem]=='A':
		return
	if result==SubmissionResult.ACCEPTED:
		user.solved+=1
		problem.solved+=1
		user.problmestatus[submission.problem]='A'
		user.penalty+=submission.time-conteststarttime
	else:
		user.problmestatus[submission.problem]='W'
		user.penalty+=submission.time-conteststarttime+timedelta(minutes=20)
	db.session.commit()



def generaterank()->list[tuple[str,int,int,list[(int,int,int)]]]:
	users=dbUser.query.all()
	users.sort(key=lambda x:(x.solved,-x.penalty))
	return users

_fixedrank=None

def queryrank():
	if datetime.now()>contestsealtime:
		return _fixedrank
	else:
		return generaterank()

def _fixrank():
	global _fixedrank
	_fixedrank=generaterank()
timer = threading.Timer(contestsealtime-datetime.now, _fixrank)
timer.start()

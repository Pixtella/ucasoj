from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from main import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.root_path + '\data.db'
db = SQLAlchemy(app)

class Problem(db.Model):
	id = db.Column(db.Integer, primary_key=True) # problem id
	name = db.Column(db.String(80), nullable=False) # problem name
	time = db.Column(db.Integer, nullable=False) # in ms
	memory = db.Column(db.Integer, nullable=False) # in MB
	solved = db.Column(db.Integer, default=0) # number of accepted submissions
	submitted = db.Column(db.Integer, default=0) # number of submissions
	# pdfpath = db.Column(db.String(256), nullable=False) # pdf path
	# datapath = db.Column(db.String(256), nullable=False) # data path

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True) # user id
	name = db.Column(db.String(80), nullable=False) # real name
	password = db.Column(db.String(80), nullable=False) # password hash
	solved = db.Column(db.Integer, default=0) # number of problems solved
	submitted = db.Column(db.Integer, default=0) # number of problems submitted
	problmestatus=db.Column(db.String(20), default="") # problem status, W for wrong, A for solved, R for running, C for compileerror, blank for not submitted
	penalty = db.Column(db.Integer, default=0) # total penalty time

class Submission(db.Model):
	id = db.Column(db.Integer, primary_key=True) # submission id
	user = db.Column(db.Integer, nullable=False) # user id
	problem = db.Column(db.Integer, nullable=False) # problem id
	submissiontime=db.Column(db.DateTime, nullable=False) # submission time
	compiler = db.Column(db.Integer, nullable=False) # compiler choice
	code = db.Column(db.String(10000), nullable=False) # code
	result = db.Column(db.Integer, default=0) # result
	compilemsg = db.Column(db.String(10000), default="") # compile message
	time = db.Column(db.Integer, default=0) # in ms
	memory = db.Column(db.Integer, default=0) # in MB

#db.drop_all()
db.create_all()

#db.session.add(Problem(id=1, name='A+B', time=1000, memory=256, pdfpath='A.pdf', datapath='A'))
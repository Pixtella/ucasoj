class Account:
    def __init__(self, id=0, username="", name=""):
        self.id = id
        self.username = username
        self.name = name

class Team:

    def __init__(self, id=0, name="", members = list()):
        self.id = id
        self.name = name
        self.members = members

class Problem:

    def __init__(self, id=0, name="", timeLimit=1000, memoryLimit=256, pdfpath=""):
        self.id = id
        self.timeLimit = timeLimit
        self.memoryLimit = memoryLimit
        self.name = name
        self.pdfpath = pdfpath

class Submision:
    def __init__(self, runid=0, problem=0, exec_time=0, exec_mem=0, language=None, user=None, result=None, code=None):
        self.runid = runid
        self.problem = problem
        self.exec_time = exec_time
        self.exec_mem = exec_mem
        self.language = language
        self.user = user
        self.result = result
        self.code = code
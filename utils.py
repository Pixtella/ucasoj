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

    def __init__(self, id=0, name="", timeLimit=1, memoryLimit=256):
        self.id = id
        self.timeLimit = timeLimit
        self.memoryLimit = memoryLimit
        self.name = name

class Submision:
    def __init__(self, runid=0, problem=0, user=None, result=None):
        self.runid = runid
        self.problem = problem
        self.user = user
        self.result = result



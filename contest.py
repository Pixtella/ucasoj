import datetime
from utils import *


class ContestProblem(Problem):
    def __init__(self, id=0, name="", timeLimit=1, memoryLimit=256, idx='A'):
        self.idx = idx
        super().__init__(id, name, timeLimit, memoryLimit)


class Contest:
    
    def __init__(self, id=1, name="Round -1", start=datetime.datetime(2000, 1, 1, 9), length=300, participants=list(), problems=list()):
        self.id = id
        self.name = name
        self.start = start
        self.length = length
        self.participants = participants
        self.problems = problems
    
    def numberofAccepted(self, problem) -> int:
        
        return 123

    def numberofAttempts(self, problem) -> int:

        return 456

    def isFirstBlood(self, team, problem):
        return True
    
    def penalty(self, team):
        """
        Penalty of a team.
        """
        return 123
    
    def solved(self, team):
        """
        Number of problems solved by team.
        """
        return 1

    def status(self, team, problem):

        return "+ 1/1" # '+': Accepted  '-': Rejected    attempts/penalty

testContestProblem = ContestProblem(1,"testProb")
t2 = ContestProblem(2, name="probB", idx='B')
testContestTeam = Team(0, "Tester",[])
testContest = Contest(1, "test Contest", datetime.datetime(2000,1,1), 300, [testContestTeam]*50, [testContestProblem, t2]*7)
testSubmission = Submision(0, 1, 123, 4567, "C", "admin", "Accepted")


def upcomingContestsInfo():
    """
    Return a list of upcoming contests.
    """

    
    return [Contest()]


def contestHistoryInfo():
    """
    Return a list of historic contests.
    """


    return [Contest()]


def retrieveContest(contestid):
    """
    Find a contest by id.
    """


    return testContest

def retrieveProblem(contestid, problemindex):
    """
    Find a problem by contestid and problem index
    """
    
    return testContestProblem

def retrieveSubmission(submissionid):
    """
    Find a submission by absolute identity
    """
    
    return testSubmission
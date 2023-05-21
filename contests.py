import datetime

class Contest:
    
    def __init__(self, id=1, name="Round -1", start=datetime.datetime(2000, 1, 1, 9), length=300, participants=list()):
        self.id = id
        self.name = name
        self.start = start
        self.length = length
        self.participants = participants
        

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
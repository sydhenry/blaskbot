'''
This is the main functions module that contains everything
we need for BlaskBot to be the most amazing thing the universe
has ever seen.

BEEP BOOP!
'''

import cfg
import requests
import time as T
import os
import sys
import socket
from tinydb import TinyDB, Query
import tinydb.operations as tdbo
from multiprocessing import Value
import xml.etree.ElementTree as ET

headers = {"Authorization":'OAuth ' + str(cfg.PASS).split(':')[1]}
# This is a global variable, but needs to be shared between timer subprocesses
# (read only, not modify) so use mp.Value()
numberOfChatMessages = Value('d', 0)

class URLError(Exception):
    pass


# ---=== HELPER FUNCTIONS ===---

def printv(msg, v):
    '''
    A custom print function that considers the set verbosity
    level before output
    Inputs:
        msg -- (str) The message
        v -- (int) The verbosity level of the message
    '''
    if cfg.VERB >= v:
        print(msg)

# ---========================---


# ---=== IRC FUNCTIONS ===---

def hostChat():
    hostSock = socket.socket()
    hostSock.connect((cfg.HOST, cfg.PORT))
    hostSock.send("PASS {}\r\n".format(cfg.PASS).encode("utf-8"))
    hostSock.send("NICK {}\r\n".format(cfg.JOIN).encode("utf-8"))
    hostSock.send("JOIN #{}\r\n".format(cfg.JOIN).encode("utf-8"))
    CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
    while True:
        response = sock.recv(1024).decode("utf-8")
        if response == "PING :tmi.twitch.tv\r\n":
            sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        message = input("Send as " + cfg.JOIN + ": ")
        chat(hostSock, message)


def chat(sock, msg):
    '''
    Sends a chat message to the server.
    Inputs:
        sock -- The socket over which to send the message
        msg -- (str) The message to send
    '''
    msg = "/me : " + msg
    printv("Sending message '" + msg + "' to chat server...", 5)
    sock.send("PRIVMSG #{} :{}\r\n".format(cfg.JOIN, msg).encode('utf-8'))


def ban(sock, user):
    '''
    Bans a user from the channel
    Inputs:
        sock -- The socket over which to send the message
        user -- (str) The name of the user to ban
    '''
    printv("Banning user '" + user + "'..." , 4)
    chat(sock, ".ban {}".format(user))


def unban(sock, user):
    '''
    Unbans/untimeouts a user from the channel
    Inputs:
        sock -- The socket over which to send the message
        user -- (str) The name of the user to ban
    '''
    printv("Unbanning user '" + user + "'..." , 4)
    chat(sock, ".unban {}".format(user))


def timeout(sock, user, time=600):
    '''
    Times a user out from the channel
    Inputs:
        sock -- The socket over which to send the message
        user -- (str) The name of the user to timeout
        time -- (int) The length of the timeout in seconds
                      (default 600)
    '''
    printv("Timing out user '" + user + "' for " + str(time) +
           " seconds..." , 4)
    chat(sock, ".timeout {}".format(user, seconds))

# ---=====================---

def threadFillOpList():
    '''
    In a separate thread, get the channel moderator list and
    keep it updated
    '''
    while True:
        viewerList = getViewerList()
        if viewerList is not None:
            VIPs = ["moderators", "staff", "admins", "global_mods"]
            for VIPType in VIPs:
                for viewer in viewerList["chatters"][VIPType]:
                    if viewer not in cfg.opList:
                        printv("Adding " + viewer + " with VIPType " +
                                VIPType + " to opList...", 4)
                        cfg.opList.append(viewer)
        T.sleep(5)


def threadUpdateDatabase(sock):
    printv("Loading the points database...", 5)
    pointsDatabase = loadPointsDatabase()
    printv("Database loaded!", 5)
    skipViewers = ['blaskatronic', 'blaskbot', 'doryx', 'fsmimp']
    previousViewers = []
    while True:
        if streamIsUp():
            printv("Stream is active. Getting viewer list...", 4)
            viewerList = getViewerList()
            if viewerList is not None:
                printv("viewerList = " + repr(viewerList), 4)
                flattenedViewerList = [viewerName for nameRank in [viewerList['chatters'][x] \
                                        for x in viewerList['chatters'].keys()] for viewerName \
                                        in nameRank]
                printv("Previous Viewers = " + repr(previousViewers), 4)
                printv("Current Viewers = " + repr(flattenedViewerList), 4)
                for viewer in flattenedViewerList:
                    if viewer in previousViewers:
                        printv(viewer + " in both lists. Adding "  + str(cfg.pointsToAward) +\
                               " points...", 5)
                        printv("Checking if " + viewer + " is in database...", 4)
                        # Check if viewer is already in the database
                        if len(pointsDatabase.search(Query().name == viewer)) == 0:
                            printv("Adding " + viewer + " to database...", 4)
                            pointsDatabase.insert({'name': viewer, 'points': 0, 'rank': 'None',
                                                   'multiplier': 1, 'lurker': True, 'totalPoints': 0})
                        printv(viewer + " has " + str(pointsDatabase.search(Query().name ==\
                                viewer)[0]['points']) + " points.", 5)
                        printv("Incrementing " + viewer + "'s points...", 4)
                        pointsDatabase.update(tdbo.add('points', cfg.pointsToAward), \
                                              Query().name == viewer)
                        # Also increment `totalPoints' which is used to keep track of
                        # view time without taking into account minigame losses
                        pointsDatabase.update(tdbo.add('totalPoints', cfg.pointsToAward), \
                                              Query().name == viewer)
                        printv("Calculating " + viewer + "'s rank...", 5)
                        currentPoints = pointsDatabase.search(Query().name == viewer)[0]['points']
                        currentTotalPoints = pointsDatabase.search(Query().name == viewer)[0]['totalPoints']
                        oldRank = pointsDatabase.search(Query().name == viewer)[0]['rank']
                        newRank = str(oldRank)
                        for rankPoints in sorted(cfg.ranks.keys()):
                            if int(currentTotalPoints) < int(rankPoints):
                                break
                            newRank = cfg.ranks[rankPoints]
                        if newRank != oldRank:
                            pointsDatabase.update(tdbo.set('rank', newRank), Query().name == viewer)
                            if (pointsDatabase.search(Query().name == viewer)[0]['lurker'] is False) and
                                (viewer not in skipViewers):
                                currencyUnits = cfg.currencyName
                                if currentPoints > 1:
                                    currencyUnits += "s"
                                chat(sock, "Congratulations " + viewer + ", you have been promoted" +\
                                     " to the rank of " + newRank + "! You now have " +\
                                     str(currentPoints) + " " + currencyUnits + " to spend!")
                        printv(viewer + " now has " + str(pointsDatabase.search(Query().name ==\
                                viewer)[0]['totalPoints']) + " points, and " str(currentPoints) " to" +\
                               " spend on minigames.", 5)
                previousViewers = flattenedViewerList[:]
        else:
            printv("Stream not currently up. Not adding points.", 4)
        printv("Database now looks like this: " + repr(pointsDatabase.all()), 5)
        T.sleep(cfg.awardDeltaT)


def loadPointsDatabase():
    pointsDB = TinyDB('./databases/' + cfg.JOIN + 'Points.db')
    return pointsDB


def loadClipsDatabase():
    clipsDB = TinyDB('./databases/' + cfg.JOIN + 'Clips.db')
    return clipsDB


def getViewerList():
    try:
        viewerURL = "http://tmi.twitch.tv/group/user/" +\
                   cfg.JOIN + "/chatters"
        viewerData = request(viewerURL, header={"User-Agent": \
            "Mozilla/5.0 (X11;Ubuntu;Linux x86_64;rv:55.0) Gecko/20100101 Firefox/55.0",\
            "Cache-Control": "max-age=0", "Connection": "keep-alive"})
        if "error" in viewerData.keys():
            raise URLError(response)
        printv("Json loaded!", 5)
        return viewerData
    except URLError as e:
        errorDetails = e.args[0]
        printv("URLError with status " + errorDetails['status'] +
               ", '" + errorDetails['error'] + "'!", 4)
        printv("Error Message: " + errorDetails['message'], 4)
        return None
    except:
        printv("Unexpected Error: " + repr(sys.exc_info()[0]), 2)
        return None


def isOp(user):
    '''
    Return a user's op status to see if they have op permissions
    '''
    return user in cfg.opList


def streamIsUp():
    streamDataURL = "https://api.twitch.tv/kraken/streams/" + cfg.JOIN
    streamData = request(streamDataURL)
    if not streamData['stream']:
        return False
    return True


def request(URL, header=headers):
    printv("Reading from URL: '" + URL + "'...", 5)
    req = requests.get(URL, headers=header)
    printv("Loading user_data json...", 5)
    return req.json()


def incrementNumberOfChatMessages():
    global numberOfChatMessages
    with numberOfChatMessages.get_lock():
        numberOfChatMessages.value += 1


def timer(command, delay, arguments):
    previousNumberOfChatMessages = 0
    try:
        exec("from commands import " + str(command))
        while True:
            # All timers must wait until 5 minutes after 1 chat message
            # has been sent before executing the command again.
            if numberOfChatMessages.value > previousNumberOfChatMessages:
                exec(str(command) + "(arguments)")
                previousNumberOfChatMessages = int(numberOfChatMessages.value)
                T.sleep(delay)
            else:
                printv("Not enough messages sent to run again (" + \
                       str(numberOfChatMessages.value) + " <= " + \
                       str(previousNumberOfChatMessages) + "). Sleeping.", 5)
                T.sleep(300)
    except (AttributeError, ImportError):
        printv("No function by the name " + command + "!", 4)


def getXMLAttributes(xmlData):
    attributeDict = {}
    elementTree = ET.fromstring(xmlData)
    for element in elementTree:
        if len(element) == 0:
            attributeDict[element.tag] = element.text
        else:
            attributeDict[element.tag] = {}
            for subelement in element:
                if subelement.tag == "category":
                    subattribute = attributeDict[element.tag][subelement.get("name")] = {}
                    for subsubelement in subelement:
                        subattribute[subsubelement.get("name")] = subsubelement.text
                else:
                    attributeDict[element.tag][subelement.tag] = subelement.text
    return attributeDict


if __name__ == "__main__":
    threadFillOpList()

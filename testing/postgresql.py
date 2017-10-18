import psycopg2
#import tinydb
from datetime import datetime
from multiprocessing import Process
import time as T
from psycopg2.extras import DictCursor
from psycopg2.extensions import AsIs

connection = None

def readRow(extra):
    #cursor.execute("SELECT Drinks FROM Viewers WHERE Name='blaskatronic'")
    #row = cursor.fetchone()
    #print(row)
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Viewers WHERE Name='blaskatronic'")
    row = cursor.fetchone()
    print(extra, row)
    connection.close()


def incrementPoints():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    while True:
        cursor.execute("UPDATE Viewers SET Points = Points + 1 WHERE Name='blaskatronic'")
        connection.commit()
        readRow("INCREMENT")
    connection.close()


def decrementPoints():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    while True:
        cursor.execute("UPDATE Viewers SET Points = Points - 2 WHERE Name='blaskatronic'")
        connection.commit()
        readRow("DECREMENT")
    connection.close()


def getClip():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    while True:
        cursor.execute("SELECT * FROM Clips WHERE ID=1")
        row = cursor.fetchone()
        connection.commit()
        print("CLIP", row)
    connection.close()


def createTables():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE Clips (ID SMALLINT PRIMARY KEY, URL VARCHAR(70), Author VARCHAR(25));")
    cursor.execute("INSERT INTO Clips VALUES (%s, %s, %s);", (1, 'YawningEnthusiasticTriangleDXAbomb', 'blaskatronic'))

    cursor.execute("CREATE TABLE Viewers (ID SMALLINT PRIMARY KEY, Name VARCHAR(25), Points SMALLINT, Rank VARCHAR(25), Multiplier FLOAT, Lurker BIT, TotalPoints SMALLINT, DrinkExpiry TIME, Drinks SMALLINT);")
    cursor.execute("INSERT INTO Viewers VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (1, 'blaskatronic', 4847, 'Prelate', 1.0, '1', 4787, datetime.now().time(), 38))


def checkViewerExists():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    viewer = 'cheeseman'
    cursor.execute("SELECT EXISTS (SELECT 1 FROM Viewers WHERE Name='" + viewer + "');")
    data = cursor.fetchone()
    print(data[0])


def getPoints(viewer='blaskatronic'):
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    cursor.execute("SELECT Points FROM Viewers WHERE name='" + viewer + "';")
    data = cursor.fetchone()
    print(data)
    return data[0]


def updatePoints():
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    viewer = 'blaskatronic'
    currentPoints = getPoints(viewer)
    readRow("BEFORE =")
    cursor.execute("UPDATE Viewers SET points=(%s) WHERE name='" + viewer + "';", tuple([currentPoints + 10]))
    cursor.execute("UPDATE Viewers SET totalpoints=(%s) WHERE name='" + viewer + "';", tuple([currentPoints + 100]))
    cursor.execute("UPDATE Viewers SET rank=(%s) WHERE name='" + viewer + "';", tuple(['Chump']))

    cursor.execute("UPDATE Viewers SET lurker=(%s) WHERE name='" + viewer + "';", tuple(['B1']))
    cursor.execute("SELECT Lurker FROM Viewers WHERE name='" + viewer + "';")
    lurkerStatus = cursor.fetchone()[0]
    print(bool(int(lurkerStatus)))
    cursor.execute("UPDATE Viewers SET lurker=(%s) WHERE name='" + viewer + "';", tuple(['B0']))
    cursor.execute("SELECT Lurker FROM Viewers WHERE name='" + viewer + "';")
    lurkerStatus = cursor.fetchone()[0]
    print(bool(int(lurkerStatus)))
    connection.commit()
    readRow("AFTER =")
    newPoints = getPoints(viewer)


def updateLurker(viewer='blaskatronic'):
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    cursor.execute("UPDATE Viewers SET lurker=(%s) WHERE name='" + viewer + "';", tuple(['B0']))
    cursor.execute("SELECT Lurker FROM Viewers WHERE name='" + viewer + "';")
    lurkerStatus = cursor.fetchone()[0]
    print(bool(int(lurkerStatus)))
    cursor.execute("UPDATE Viewers SET lurker=(%s);", tuple(['B1']))
    cursor.execute("SELECT Lurker FROM Viewers WHERE name='" + viewer + "';")
    lurkerStatus = cursor.fetchone()[0]
    print(bool(int(lurkerStatus)))


def getBoth(viewer='blaskatronic'):
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    cursor.execute("SELECT (points, totalPoints) FROM Viewers WHERE name='" + viewer + "';")
    data = cursor.fetchone()[0]
    print(eval(data))
    (currentPoints, currentTotalPoints) = eval(data)
    print(currentPoints, currentTotalPoints)


def buyDrink(viewer='blaskatronic'):
    connection = psycopg2.connect(database='testdb', user='blaskbot')
    cursor = connection.cursor()
    numberOfDrinks = 5
    cursor.execute("SELECT Drinks FROM Viewers WHERE name='" + viewer + "';")
    currentDrinks = cursor.fetchone()[0]
    print(currentDrinks)
    print(cursor.mogrify("UPDATE Viewers SET drinks=drinks + " + str(numberOfDrinks) + " WHERE name='" + viewer.lower() + "';"))
    cursor.execute("UPDATE Viewers SET drinks=drinks + " + str(numberOfDrinks) + " WHERE name='" + viewer.lower() + "';")
    cursor.execute("SELECT Drinks FROM Viewers WHERE name='" + viewer + "';")
    currentDrinks = cursor.fetchone()[0]
    print(currentDrinks)


def getRandomClip():
    connection = psycopg2.connect(database='blaskatronic', user='blaskbot')
    cursor = connection.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM Clips")
    clips = cursor.fetchall()
    index = -1
    print(clips[index]['url'])


def getTop():
    connection = psycopg2.connect(database='blaskatronic', user='blaskbot')
    forbidden = ['blaskatronic', 'blaskbot', 'doryx']
    cursor = connection.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM Viewers WHERE name NOT IN (" + ', '.join([repr(x) for x in forbidden]) + ") ORDER BY totalpoints DESC LIMIT 10;")
    topRanked = cursor.fetchall()
    for i, viewerDetails in enumerate(topRanked):
        #print(i, "|", viewerDetails['name'], "|", viewerDetails['totalpoints'])
        print("%1d | %15s | %5d" % (i, viewerDetails['name'], viewerDetails['totalpoints']))


def fixViewerDB():
    connection = psycopg2.connect(database='blaskytest', user='blaskbot')
    forbidden = ['blaskatronic', 'blaskbot', 'doryx']
    cursor = connection.cursor()
    viewer = 'chumpzilla'
    insert = {'Name': viewer.lower(), 'Points': 0, 'Rank': 'Chump',
              'Multiplier': 1.0, 'Lurker': 'B1', 'TotalPoints': 0,
              'Drinks': 0, 'Discord': viewer.lower()}
    cursor.execute("INSERT INTO Viewers (%s) VALUES %s;", (AsIs(', '.join(insert.keys())), AsIs(tuple(insert.values()))))
    cursor.execute("SELECT * FROM Viewers WHERE name='" + viewer.lower() + "';")
    currentViewer = cursor.fetchone()
    print(currentViewer)




if __name__ == "__main__":
    #try:
    #    #createTables(cursor)
    #    readRow("INIT")
    #    incrementPoints = Process(target=incrementPoints, args=(), daemon=True)
    #    decrementPoints = Process(target=decrementPoints, args=(), daemon=True)
    #    getClip = Process(target=getClip, args=(), daemon=True)
    #    input("ARE YOU READY?!")
    #    incrementPoints.start()
    #    decrementPoints.start()
    #    #getClip.start()
    #    T.sleep(0.05)
    #    exit()
    #    #incrementPoints(cursor)
    #    #connection.commit()
    #    input("WAIT")

    #except psycopg2.DatabaseError as e:
    #    if connection:
    #        connection.rollback()
    #    print("Error", e)
    #    exit()


    #checkViewerExists()
    #updatePoints()
    #updateLurker()
    #getBoth()
    #buyDrink()
    #getRandomClip()
    #getTop()
    fixViewerDB()

    if connection:
        connection.close()

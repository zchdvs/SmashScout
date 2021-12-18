from datetime import datetime
from sqlite3.dbapi2 import IntegrityError
import apitoken
import sqlite3
import time
#pip install --pre gql[all]
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

templateQueryWATournaments = """
{
  tournaments(query:{
    sortBy: "startAt desc"
    perPage: 100
    page: xpageNumx
      filter: {
        addrState: "WA"
      }
    }) {
    nodes 
      {
        id
        name
        slug
        numAttendees
        startAt
        endAt        
      }
    }
}
"""
def initializeSmashGGConnection():
    smashGG_Token = apitoken.smashGG_Token
    transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)
    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

def initializeSQLiteDB():
    dbInstance = sqlite3.connect('tournamentinfo.db')
    return dbInstance

    #commits any other changes if any and closes
def uninitializeSQLiteDB(db):
    db.commit()
    db.close()

#80 queries over 60 seconds. Less than 1000 objects per query
def waitRateLimit():
    time.sleep(0.8)

def queryClient(client, query):
    result = client.execute(gql(query))
    waitRateLimit()
    return result

#add all new tournaments to the database
#returns list of the tournaments to be used in updating players as well
def updateTournaments(client, db):
    newTournaments = {}
    pageNum = 0
    while True:
        queryWATournamentPage = templateQueryWATournaments.replace("xpageNumx", str(pageNum))
        result = queryClient(client, queryWATournamentPage)
        numTournaments = len(result['tournaments']['nodes'])
        if numTournaments == 0:
            print("no tournaments found, exiting loop")
            break
        tournamentPage = result['tournaments']['nodes']
        #merging the tournaments dictionaries from storeTournamentsPage
        newTournaments.update(storeTournamentPage(tournamentPage, db))

        pageNum += 1
        break
    return newTournaments


def storeTournamentPage(tournamentPage, db):
    dbCursor = db.cursor()
    storedTournaments = {}
    for tournament in tournamentPage:
        print(tournament)
        try:
            dbCursor.execute("INSERT INTO tournaments VALUES (?,?,?,?,?,?)", (tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt']))
        except sqlite3.IntegrityError:
            print("tournament already exists ID:" + str(tournament['id']) + " NAME: " + tournament['name'])
            continue
        #(tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt'])
        db.commit()
        #add to the storedTournaments dictionary if not pre-existing
        if not storedTournaments.has_key(tournament['id']):
            storedTournaments[tournament['id']] = [tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt']]
    return storedTournaments

def updatePlayers(tournaments, client, db):
    print()

def findTournamentPlayers(tournament):
    print()



smashggClient = initializeSmashGGConnection()
sqliteDB = initializeSQLiteDB()
tournamentList = updateTournaments(smashggClient, sqliteDB)
updatePlayers(tournamentList, smashggClient, sqliteDB)







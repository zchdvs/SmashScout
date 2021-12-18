from datetime import datetime
from sqlite3.dbapi2 import IntegrityError
import apitoken
import sqlite3
import time
#pip install --pre gql[all]
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import logging

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

templateQueryWATournamentPlayers = """
{
  tournaments(query: {
    perPage: 1
    page: 1
    filter:{
      id: xIDx
    }
  }) 
  {
    nodes
    {
      name
      participants(query: {
        perPage: 75
        page: xpageNumx
        sortBy: "seed"
      })
      {
        nodes
        {
          id
          connectedAccounts
          gamerTag
          player
          {
            id
            gamerTag
          }
          user
          {
            id
            name
            slug
            authorizations
            {
              externalId
              externalUsername
              type
              url
            }   
          }
        }
      }
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
    dbInstance.execute("CREATE TABLE IF NOT EXISTS tournaments (id INTEGER PRIMARY KEY, name TEXT, slug TEXT, numAttendees INTEGER, startDate INTEGER, endDate INTEGER)")
    dbInstance.execute("CREATE TABLE IF NOT EXISTS playermap (id INTEGER, gamertag TEXT UNIQUE)")
    dbInstance.execute("CREATE TABLE IF NOT EXISTS playerinfo (id INTEGER PRIMARY KEY, name TEXT, userslug TEXT, userID INTEGER, linkedAccounts TEXT, authorizations TEXT)")
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
            logging.info("no tournaments left, exiting loop")
            break
        tournamentPage = result['tournaments']['nodes']
        #print(tournamentPage)
        #merging the tournaments dictionaries from storeTournamentsPage
        storedTournaments = storeTournamentPage(tournamentPage, db)
        newTournaments.update(storedTournaments)
        #print(newTournaments)
        pageNum += 1
    return newTournaments


def storeTournamentPage(tournamentPage, db):
    dbCursor = db.cursor()
    storedTournaments = {}
    for tournament in tournamentPage:
        #print("TOURNAMENT")
        #print(tournament)
        logging.info('working on tournament %s', str(tournament['id']))
        try:
            dbCursor.execute("INSERT INTO tournaments VALUES (?,?,?,?,?,?)", (tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt']))
        except sqlite3.IntegrityError:
            errMsg = "tournament already exists ID:" + str(tournament['id']) + " NAME: " + tournament['name']
            logging.info(errMsg)
            continue
        #(tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt'])
        db.commit()
        #add to the storedTournaments dictionary if not pre-existing
        print("STOREDTOURNAMENTS")
        print(storedTournaments)
        if (tournament['id']) not in storedTournaments:
            print("adding" + str(tournament['id']) )
            storedTournaments[str(tournament['id'])] = [tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt']]
    print(storedTournaments)
    return storedTournaments


def updatePlayers(tournaments, client, db):
    for tournament in tournaments:
        pageNum = 0
        while(True):
            queryWATournamentPlayers = templateQueryWATournamentPlayers.replace('xIDx', str(tournament)).replace('xpageNumx', str(pageNum))
            result = queryClient(client, queryWATournamentPlayers)
            numParticipants = len(result['tournaments']['nodes'][0]['participants']['nodes'])
            if numParticipants == 0:
                logging.info("0 participants found for tournament %s", str(tournament))
                break
            participants = result['tournaments']['nodes'][0]['participants']['nodes']
            for participant in participants:
                storeTournamentPlayer(participant, db)
            db.commit()
            pageNum += 1

def storeTournamentPlayer(participant, db):
    if(participant['user'] == None):
        logging.info('user missing, %s', str(participant['player']['id']))
        userid = -1
        name = ''
        slug = ''
        authorizations = []
    else:
        userid = participant['user']['id']
        name = participant['user']['name']
        slug = participant['user']['slug']
        authorizations= participant['user']['authorizations']
    
    gamerTag = participant['gamerTag']
    playerTag = participant['player']['gamerTag']
    playerID = participant['player']['id']
    linkedAccounts = participant['connectedAccounts']
    if linkedAccounts == None:
        linkedAccounts = {}
    db.execute("INSERT OR IGNORE INTO playermap VALUES (?,?)", (playerID,playerTag))
    if gamerTag != playerTag:
        db.execute("INSERT OR IGNORE INTO playermap VALUES (?,?)", (playerID,gamerTag))
        logging.info('multiple usernames for %s, (%s,%s)',str(participant['player']['id']),playerID,gamerTag)

    try:
        db.execute("INSERT INTO playerinfo VALUES (?,?,?,?,?,?)", (playerID,name,slug,userid,str(linkedAccounts),str(authorizations)))
    except sqlite3.IntegrityError as errMsg:
        logging.info("player info already exists %s", playerID)

def initializeLogging():
    logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO)

initializeLogging()
logging.info("Initializing")
smashggClient = initializeSmashGGConnection()
sqliteDB = initializeSQLiteDB()
logging.info("Looking at Tournaments")
tournamentList = updateTournaments(smashggClient, sqliteDB)
print(tournamentList)
logging.info("Looking at Players")
updatePlayers(tournamentList, smashggClient, sqliteDB)
logging.info("Unitiializing")
uninitializeSQLiteDB(sqliteDB)
logging.info("Finished Updating Player Base")








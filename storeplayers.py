
from datetime import datetime
import apitoken
import sqlite3
import time

smashGG_Token = apitoken.smashGG_Token

#pip install --pre gql[all]
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

#connect to sqlite db
dbInstance = sqlite3.connect('tournamentinfo.db')

dbCursor = dbInstance.cursor()

if(dbCursor.connection != dbInstance):
  print("connection to DB failed. exiting")
  exit

print("checking if table \'tournaments\' exist?")
#check if the tournament table exists
listoftables = dbCursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tournaments';").fetchall()
if(len(listoftables) == 0):
  print("no table found. exiting")
  exit

print("Querying Table")

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
        perPage: 100
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

#create the user id --> gamertag table
#separate for faster querying of gamertag (and due to the possibility of multiple gamertags)
dbCursor.execute("CREATE TABLE IF NOT EXISTS playermap (id INTEGER, gamertag TEXT)")

#create the user id --> info table
#once we have found appropriate id for a gamertag
dbCursor.execute("CREATE TABLE IF NOT EXISTS playerinfo (id INTEGER PRIMARY KEY, name TEXT, userslug TEXT, playerID INTEGER, linkedAccounts TEXT, authorizations TEXT)")

tagDiscrepancy= []
missingUsers = []
newTagNum = 0
newUserInfoNum = 0

for row in dbCursor.execute("SELECT * FROM tournaments ORDER BY startDate DESC"):
  pageNum = 0
  print(row[0])
  while(True):
    queryWATournamentPlayers = templateQueryWATournamentPlayers.replace('xIDx', str(row[0])).replace('xpageNumx', str(pageNum))
    print(queryWATournamentPlayers)
    result = client.execute(gql(queryWATournamentPlayers))
    print()
    print(result['tournaments']['nodes'][0]['name'])
    print(len(result['tournaments']['nodes'][0]['participants']['nodes']))
    print()
    if(len(result['tournaments']['nodes'][0]['participants']['nodes']) == 0):
      break
    for participant in result['tournaments']['nodes'][0]['participants']['nodes']:
      if(participant['user'] == None):
        missingUsers.append(participant)
        continue
      print(participant)
      userid = participant['user']['id']
      gamerTag = participant['gamerTag']
      playerTag = participant['player']['gamerTag']
      #checking and storing discrepancies to read at the end

      #try to add mapping (unless pre-existing)
      try:
        dbInstance.execute("INSERT INTO playermap VALUES (?,?)", (userid,playerTag))
        newTagNum +=1
      except sqlite3.IntegrityError:
        print("mapping already exists, skipping")
      
      if gamerTag != playerTag:
        tagDiscrepancy.append([gamerTag,playerTag])
        try:
          dbInstance.execute("INSERT INTO playermap VALUES (?,?)", (userid,gamerTag))
          newTagNum +=1
        except sqlite3.IntegrityError:
          print("mapping already exists, skipping")

      #playerinfo (id INTEGER PRIMARY KEY, name TEXT, userslug TEXT, playerID INTEGER, linkedAccounts TEXT, authorizations TEXT)"
      name = participant['user']['name']
      slug = participant['user']['slug']
      playerID = participant['player']['id']
      linkedAccounts = participant['connectedAccounts']
      authorizations= participant['user']['authorizations']
      if(linkedAccounts == None):
        linkedAccounts = {}
      print(linkedAccounts)
      print(authorizations)
      try:
        dbInstance.execute("INSERT INTO playerinfo VALUES (?,?,?,?,?,?)", (userid,name,slug,playerID,str(linkedAccounts),str(authorizations)))
        newUserInfoNum += 1
      except sqlite3.IntegrityError:
        print("mapping already exists, skipping")
      #try to store data (unless pre-existing)
    dbInstance.commit()
    time.sleep(0.8)
    pageNum += 1
  dbInstance.commit()

print("Missing Users")
print(missingUsers)
print("DISCREPANCIES")
print(tagDiscrepancy)
print("New tags")
print(newTagNum)
print("new user info")
print(newUserInfoNum)
dbInstance.close()
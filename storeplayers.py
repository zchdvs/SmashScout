from datetime import datetime
import apitoken
import sqlite3
import time
import pandas as pd
import json

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

#create the player id --> gamertag table
#separate for faster querying of gamertag (and due to the possibility of multiple gamertags)
dbCursor.execute("CREATE TABLE IF NOT EXISTS playermap (id INTEGER, gamertag TEXT UNIQUE)")

#create the player id --> info table
#once we have found appropriate id for a gamertag
dbCursor.execute("CREATE TABLE IF NOT EXISTS playerinfo (id INTEGER PRIMARY KEY, name TEXT, userslug TEXT, userID INTEGER, linkedAccounts TEXT, authorizations TEXT)")

tagDiscrepancy= []
missingUsers = []
newTagNum = 0
newUserInfoNum = 0

errorEntries = []
numTourney = 0
for row in dbCursor.execute("SELECT * FROM tournaments ORDER BY startDate DESC"):
  tournamentID = row[0]
  pageNum = 0
  print(row[0])
  while(True):
    queryWATournamentPlayers = templateQueryWATournamentPlayers.replace('xIDx', str(tournamentID)).replace('xpageNumx', str(pageNum))
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
        missingUsers.append([tournamentID, pageNum,participant])
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
      #checking and storing discrepancies to read at the end

      #playerinfo (id INTEGER PRIMARY KEY, name TEXT, userslug TEXT, playerID INTEGER, linkedAccounts TEXT, authorizations TEXT)"

      playerID = participant['player']['id']
      linkedAccounts = participant['connectedAccounts']
      if(linkedAccounts == None):
        linkedAccounts = {}
      print(linkedAccounts)
      print(authorizations)

      #try to add mapping (unless pre-existing)
      
      dbInstance.execute("INSERT OR IGNORE INTO playermap VALUES (?,?)", (playerID,playerTag))
      newTagNum +=1
      
      if gamerTag != playerTag:
        tagDiscrepancy.append([tournamentID, pageNum, [gamerTag, playerTag]])
        dbInstance.execute("INSERT OR IGNORE INTO playermap VALUES (?,?)", (playerID,gamerTag))
        newTagNum +=1


      try:
        dbInstance.execute("INSERT INTO playerinfo VALUES (?,?,?,?,?,?)", (playerID,name,slug,userid,str(linkedAccounts),str(authorizations)))
        newUserInfoNum += 1
      except sqlite3.IntegrityError as errMsg:
        errorEntries.append([tournamentID, pageNum, playerID, userid, errMsg.args])
        print("mapping already exists, skipping")
      #try to store data (unless pre-existing)
    dbInstance.commit()
    time.sleep(0.8)
    pageNum += 1
  dbInstance.commit()


dbInstance.close()
# print("Missing Users")
# print(missingUsers)
# print("DISCREPANCIES")
# print(tagDiscrepancy)
# print("New tags")
# print(newTagNum)
# print("new user info")
# print(newUserInfoNum)

#pd.DataFrame(errorEntries).to_json(r'errorentries.json', orient = 'records')
#pd.DataFrame(missingUsers).to_json(r'missingusers.json', orient = 'records')
#pd.DataFrame(tagDiscrepancy).to_json(r'tagdiscrepancy.json', orient = 'records')
with open('errorentries.json', 'w') as output:
  json.dump(errorEntries, output)
with open('missingusers.json', 'w') as output:
  json.dump(missingUsers, output)
with open('tagdiscrepancy.json', 'w') as output:
  json.dump(tagDiscrepancy, output)



  


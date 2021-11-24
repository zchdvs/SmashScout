from datetime import datetime
import apitoken
import sqlite3
import time
#pip install --pre gql[all]
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


smashGG_Token = apitoken.smashGG_Token
transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

dbInstance = sqlite3.connect('tournamentinfo.db')
#Let’s store the tournament ID, name, slug, attendees, startAt, endAt, 
createTable = '''CREATE TABLE tournaments (id INTEGER PRIMARY KEY, name TEXT, slug TEXT, numAttendees INTEGER, startDate INTEGER, endDate INTEGER)'''

try:
  dbInstance.execute(createTable)

except sqlite3.OperationalError:
  print("tournament table already exists. continuing")

dbCursor = dbInstance.cursor()

if(dbCursor.connection != dbInstance):
  print("connection to DB failed. exiting")
  exit

#https://developer.smash.gg/docs/examples/queries/tournaments-by-videogame/
#https://docs.google.com/spreadsheets/d/1l-mcho90yDq4TWD-Y9A22oqFXGo8-gBDJP0eTmRpTaQ/edit#gid=1924677423
#can filter by videogameID if desired (maybe smash ultimate and melee for now?)
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

numNewTournaments = 0
pageNum = 0
#tournamentInDB = False
while True:
  pageNumString = str(pageNum)
  print("storing page " + pageNumString)
  queryWATournaments = templateQueryWATournaments.replace("xpageNumx", pageNumString)
  print(queryWATournaments)
  #testQueryWATournament
  result = client.execute(gql(queryWATournaments))
  #rate limit 60 seconds / 80 queries is 0.75, round to 8 for safety
  print(len(result['tournaments']['nodes']))
  pageNum += 1

  if(len(result['tournaments']['nodes']) == 0):
    #break if there are no more tournaments
    break
  #
  numNewTournamentsThisPage = 0
  print('')
  time.sleep(0.8)
  for tournament in result['tournaments']['nodes']:
    print(tournament)
    tournamentInfo = []
    #tournament ID, name, slug, attendees, startAt, endAt, 
    #insertionString = '''INSERT INTO tournaments VALUES({id}, \'{name}\', \'{slug}\', {numAttendees}, {startDate}, {endDate} )'''.format( id=tournament['id'],name=tournament['name'].replace("\'", "\\\'"), slug=tournament['slug'], numAttendees=tournament['numAttendees'], startDate=tournament['startAt'], endDate = tournament['endAt'] )
    #print(insertionString)
    try:
      #dbInstance.execute(insertionString)
      dbCursor.execute("INSERT INTO tournaments VALUES (?,?,?,?,?,?)", (tournament['id'], tournament['name'], tournament['slug'], tournament['numAttendees'], tournament['startAt'], tournament['endAt']))
      numNewTournamentsThisPage += 1
      
    except sqlite3.IntegrityError:
      print("tournament already exists ID:" + str(tournament['id']) + " NAME: " + tournament['name'])
      continue
  numNewTournaments += numNewTournamentsThisPage
  dbInstance.commit()
  if(numNewTournamentsThisPage < 1):
    #if no new tournaments from 100 of this page, it's probably safe to end early
    print("ending iteration early, page had no new tournaments. Likely no new tournaments beyond this")
    break

dbInstance.commit()
#while len(result['tournaments']['nodes']) 

print("Page has " + str(len(result['tournaments']['nodes'])) + " tournaments")
print(str(numNewTournaments) + " added.")
print("closing DB")

dbInstance.close()
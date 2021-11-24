
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
if(len(listoftables) != 0):
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
  nodes
    {
      name
      slug
      addrState
      city
      countryCode
      endAt
      participants(query: {
        perPage: 100
        page: xpageNumx
        sortBy: "seed"
      }) {
        node 
        {
          id
          connectedAccounts
          player
        }
      }
    }
}
"""

pageNum = 0
for row in dbCursor.execute("SELECT * FROM tournaments ORDER BY startDate DESC"):
  print(row[0])
  queryWATournamentPlayers = templateQueryWATournamentPlayers.replace('xIDx', row[0]).replace('xpageNumx', str(pageNum))
  print(queryWATournamentPlayers)
  result = client.execute(gql(queryWATournamentPlayers))

  time.sleep(0.8)
  #print(row)

  

testQueryWATournamentPlayers = """
    tournaments(query:{
      perPage: 100
      page: 1
      filter: {
        addrState: "WA"
      }
    }) {
      nodes 
      {
        id
        countryCode
        name
        numAttendees
        slug
        venueName
        venueAddress
      }
    }
  }
"""

"""
  tournaments(query: {
    perPage: 1
    page: 1
    filter:{
      id: 211228
    }
  nodes
    {
      name
      slug
      addrState
      city
      countryCode
      endAt
      participants(query: {
        perPage: 100
        page: 2
        sortBy: "seed"
      })
      {
        nodes
"""

dbInstance.close()
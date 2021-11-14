from sqlite3.dbapi2 import OperationalError
from flask import Flask, render_template, request
from datetime import datetime
import json
import apitoken
import sqlite3
import time

smashGG_Token = apitoken.smashGG_Token


from gql import gql, Client
#from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

# Select your transport with a defined url endpoint
#transport = AIOHTTPTransport(url="http://smash.gg/", headers={'Authorization': smashGG_Token}   )
transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

#Let's figure out how to query a specific player
#queries for players are by ID, so we would need to first map all players to an ID, and periodically update this
#players has user, and user has tournaments
#so to create the dictionary, we would first need to loop through all tournaments, get all the participants, and then get player gamertag, id, user id, name, and slug.
#can store these locally on a file as a csv, and then parse that everytime for easy access

#we actually need to loop through and get all tournaments, from there, we can do another query for each tournamnet

#1263 tournaments at this point

testQueryWATournament = """
{
  tournaments(query:{
      perPage: 100
      page: 13
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


dbInstance = sqlite3.connect('tournamentinfo.db')
#Let’s store the tournament ID, name, slug, attendees, startAt, endAt, 
createTable = '''CREATE TABLE tournaments (id INTEGER PRIMARY KEY, name TEXT, slug TEXT, numAttendees INTEGER, startDate INTEGER, endDate INTEGER)'''

try:
  dbInstance.execute(createTable)

except sqlite3.OperationalError:
  print("tournament table already exists. continuing")

dbCursor = dbInstance.cursor()

if(dbCursor.connection != dbInstance):
  print("connection failed. exiting")
  exit

templateQueryWATournaments = """
{
  tournaments(query:{
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

pageNum = 0
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
    except sqlite3.IntegrityError:
      print("tournament already exists ID:" + str(tournament['id']) + " NAME: " + tournament['name'])
      continue 

  dbInstance.commit()




#while len(result['tournaments']['nodes']) 

print(len(result['tournaments']['nodes']))
print("")










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




#will need to figure out fprint so we can add page to each query


testQueryPlayerInformation = """
"""

#a search function for names would be nice, but very extra, let's assume at this point that they have the correct smashgg name that they want to look at
#for a given user, display all tournaments

#for a given user display all tournament videos involving them
#this can be multiple youtube queries with smash, tournament name, and then player name.
#will need a way to figure out how accurate this is

#result = client.execute(gql(testQueryWATournamentPlayers))
#print(result)
dbInstance.close()
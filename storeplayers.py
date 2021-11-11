from flask import Flask, render_template, request
from datetime import datetime
import json
import apitoken

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


#singular at this point

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

#will need to figure out fprint so we can add page to each query


testQueryPlayerInformation = """
"""

#a search function for names would be nice, but very extra, let's assume at this point that they have the correct smashgg name that they want to look at
#for a given user, display all tournaments

#for a given user display all tournament videos involving them
#this can be multiple youtube queries with smash, tournament name, and then player name.
#will need a way to figure out how accurate this is

result = client.execute(gql(testQueryWATournamentPlayers))
print(result)
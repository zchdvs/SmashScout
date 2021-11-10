from flask import Flask, render_template
from datetime import datetime

import apitoken

smashGG_Token = apitoken.smashGG_Token

app = Flask(__name__)

#https://smash.gg/tournament/port-priority-6/details
# smashGG graphQL Ex:
# query SocalTournaments($perPage: Int, $coordinates: String!, $radius: String!) {
#   tournaments(query: {
#     perPage: $perPage
#     filter: {
#       location: {
#         distanceFrom: $coordinates,
#         distance: $radius
#       }
#     }
#   }) {
#     nodes {
#       id
#       name
#       city
#     }
#   }
# },
# {
#   "perPage": 4,
#   "coordinates": "33.7454725,-117.86765300000002",
#   "radius": "50mi"
# }




from gql import gql, Client
#from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

# Select your transport with a defined url endpoint
#transport = AIOHTTPTransport(url="http://smash.gg/", headers={'Authorization': smashGG_Token}   )
transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

# Provide a GraphQL query
query = gql(
    """
{tournaments(query: {
    perPage: 4
    filter: {
      location: {
        distanceFrom: "33.7454725,-117.86765300000002",
        distance: "5mi"
      }
    }
  }) {
    nodes {
      id
      name
      city
    }
  }
}
""")


#let's start with getting Port Priority 6

testTournamentQuery = """
{
  tournaments(query:{
    perPage: 5
    filter: {
      addrState: "WA"
      afterDate: 1635145200
      beforeDate: 1635836400
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
query TournamentsByState($perPage: Int, $state: String!) {
  tournaments(query: {
    perPage: $perPage
    filter: {
      addrState: $state
    }
  }) {
    nodes {
      id
      name
      addrState
    }
  }
},
{
  "perPage": 4,
  "state": "CT"
}
"""

#let's try getting user
testQueryUser = """
{
  user(query: 
  {

  })

}
"""

testZachQuery = """
{tournaments(query: {
    perPage: 4
    filter: {
      addrState: "WA"
    }
  }) 
  {
    nodes 
    {
      id
      name
      city
      participants(query: {
        perPage: 25,
      }) 
      {
      nodes{
        user{
          slug
          player{
            gamerTag
          }
          id
          name
          location{
            city
          }
          authorizations{
          externalUsername
          type
          }
        }
      }
      }
    }
  }
}
"""

testPortPriorityQuery = """
{
  tournaments(query: {
    perPage: 1
    page: 1
    filter:{
      id: 211228
    }
  }) 
  {
  nodes
    {
      name
      slug
      addrState
      city
      countryCode
      endAt
      links
      {
        facebook
        discord
      }
      participants(query: {
        perPage: 100
        page: 2
      })
      {
        nodes
        {
          user
          {
            id
            name
            slug
            player
            {
              id
              gamerTag
            }
            authorizations
            {
              externalUsername
              type
              url
            }            
          }
          contactInfo
          {
            id
            city
            country
            countryId
            name
            nameFirst
            nameLast
            state
            stateId
            zipcode
          }
          connectedAccounts
          email
        }
      }        
    }
  }
}
"""

# result = client.execute(gql(testPortPriorityQuery))
# print(result)

#eventually raw JSON FORM and then we can just stringify

@app.route("/")
def sscoutHome():
  return render_template('index.html')
if __name__ == "__main__":
    app.run(debug=True)
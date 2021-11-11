from flask import Flask, render_template, request
from datetime import datetime
import json
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
    perPage: 10
    filter: {
      location: {
        distanceFrom: "%s",
        distance: "%s"
      }
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
        sortBy: "seed"
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
tournamentByRadiusQueryStr = """
{
  tournaments(query: {
    perPage: 10
    page: %s
    sortBy: "startAt asc"
    filter: {
      location: {
        distanceFrom: "%s",
        distance: "%s"
      }
      upcoming: true
    }
  }) 
  {
  nodes
    {
      name
      url
      id
      addrState
      images
        {
        url
        type
        }
      city
      countryCode
      isRegistrationOpen
      startAt
      endAt
      links
      {
        facebook
        discord
      }      
    }
  }
}
"""
playersByTournamentIdQueryStr = """
{
  tournaments(query: {
    filter: {
      id: %s
    }
  }) 
  {
  nodes
    {
      name
      url
      id
      addrState
      images
        {
        url
        type
        }
      city
      countryCode
      isRegistrationOpen
      startAt
      endAt
      links
      {
        facebook
        discord
      }
       participants(query: {
        perPage: 100
        page: 1
        sortBy: "seed"
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

#Let's figure out how to query a specific player
#queries for players are by ID, so we would need to first map all players to an ID, and periodically update this
#players have user, and user has tournaments
#so to create the dictionary, we would first need to loop through all tournaments, get all the participants, and then get player gamertag, id, user id, name, and slug.
#can store these locally on a file as a csv, and then parse that everytime for easy access

testQueryPlayerInformation = """
"""

#a search function for names would be nice, but very extra, let's assume at this point that they have the correct smashgg name that they want to look at
#for a given user, display all tournaments

#for a given user display all tournament videos involving them
#this can be multiple youtube queries with smash, tournament name, and then player name.
#will need a way to figure out how accurate this is

# result = client.execute(gql(testPortPriorityQuery))
# print(result)

#eventually raw JSON FORM and then we can just stringify

@app.route("/")
def sscoutHome():
  if 'tournament' in request.args:
    transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    tournamentID = request.args.get('tournament')
    query = playersByTournamentIdQueryStr % (str(tournamentID))
    queryResultDict = client.execute(gql(query))
    tournament = queryResultDict['tournaments']['nodes'][0]
    print(queryResultDict)
    return render_template('tournamentAnalyze.html', 
                            tournamentStartDate = datetime.fromtimestamp(tournament['startAt']).strftime("%x"),
                            tournamentName = tournament['name'],
                            tournamentDescription = "",
                            tournamentImageURL = tournament['images'][0]['url']
                          )

  else:
    return render_template('index.html')

@app.route("/sscoutAPI/smashgg" , methods = ['POST'])
def sscoutAPI_Smashgg():
  transport = RequestsHTTPTransport(url="https://api.smash.gg/gql/alpha", headers={'Authorization': smashGG_Token}, use_json=True)
  # Create a GraphQL client using the defined transport
  client = Client(transport=transport, fetch_schema_from_transport=True)
  if request.form.get("type") == 'TournamentsByCoords':
    result = ""
    coords = request.form.get('coordinates')
    radius = request.form.get("radius")
    page = request.form.get("page")
    print(radius, coords)
    query = tournamentByRadiusQueryStr % (page, coords, radius)
    #oh damn this actually returns a dict
    queryResultDict = client.execute(gql(query))
    print(queryResultDict)
    # article format from html template
    # <article>
    # 	<header>
    # 		<span class="date">April 24, 2017</span>
    # 		<h2><a href="#">Sed magna<br />
    # 		ipsum faucibus</a></h2>
    # 	</header>
    # 	<a href="#" class="image fit"><img src="/static/images/pic02.jpg" alt="" /></a>
    # 	<p>Donec eget ex magna. Interdum et malesuada fames ac ante ipsum primis in faucibus. Pellentesque venenatis dolor imperdiet dolor mattis sagittis magna etiam.</p>
    # 	<ul class="actions special">
    # 		<li><a href="#" class="button">Full Story</a></li>
    # 	</ul>
    # </article>


    html = ""
    for tournament in queryResultDict['tournaments']['nodes']:
      imgUrl = " "
      if len(tournament['images']) > 0:
        if type(tournament['images'][0]['url']) != 'NoneType':
          imgUrl = tournament['images'][0]['url']
      try:  
        html += """
            <article>
              <header>
                <h2><a href="?tournament="""+str(tournament['id'])+"""">"""+tournament['name']+"""</a></h2>
                <h3>"""+datetime.fromtimestamp(tournament['startAt']).strftime("%x")+"""</h3>
                <h3>"""+tournament['city']+ ", " +tournament['addrState']+"""</h3>
              </header>
              <a href="?tournament="""+str(tournament['id'])+"""" class="image fit"><img src=" """+ imgUrl +""" " alt="" style="max-width: 300px; margin: auto;"></a>
            </article>"""
      except Exception as e:
        print(repr(e))
  return html

if __name__ == "__main__":
    app.run(debug=True)
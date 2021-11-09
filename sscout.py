
smashGG_Token = "Bearer d8d8a83ccc5816aab490c4a0da63128f"
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
result = client.execute(query)
print(result)
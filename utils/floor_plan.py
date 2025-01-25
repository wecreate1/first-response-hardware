from utils.urequest import urlopen
from utils.load_env import load_env

env = load_env()
server_url = env.get("SERVER_URL")
node_id = env.get("NODE_ID")

def get_floor_plan(floor_id, headers=None, ws=None):
  if floor_id is None:
    return "{}"

  url = f"http://{server_url}/graphql"
  query = """
    query($floorId: ID!){
      getFloorPlan(id: $floorId) {
        id
        name
        nodes {
          id
          name
          state
          isExit
          ui {
            x
            y
          }
          connections {
            id
            name
            direction
          }
        }
      }
    }
  """
  variables = {"floorId": floor_id}
  data = {
    "query": query,
    "variables": variables
  }
  if headers is None:
    headers = {}
  copied_headers = headers.copy()
  copied_headers["Content-Type"] = "application/json"
  print(copied_headers)
  response = urlopen(url, data=data, method="POST", headers=copied_headers)
  return response

# def set_node_on_fire(floor_name, node_name, headers = None):
#   if floor_name is None or node_name is None:
#     return "{}"
  
#   node_data = {}
#   node_data["id"] = node_id
#   node_data["name"] = node_name
#   node_data["operation"] = "update"
#   node_data["state"] = "compromised"

#   url = f"https://{server_url}/graphql"

#   query = """
#     mutation($floorData: CreateFloorInput!) {
#       createFloor(createFloorInput: $floorData) {
#         id
#       }
#     }
#   """

#   variables = {
#     "floorData": {
#       "name": floor_name,
#       "nodes": [
#         node_data
#       ]
#     }
#   }

#   data = {
#     "query": query,
#     "variables": variables
#   }
#   if headers is None:
#     headers = {}
#   copied_headers = headers.copy()
#   print(copied_headers)
#   copied_headers["Content-Type"] = "application/json"
#   response = urlopen(url, data=data, method="POST", headers=copied_headers)
#   print(response)
#   return response
import json
import _thread
import time
from machine import Pin
from utils.load_env import load_env
from utils.connect_wifi import connect_to_wifi
from utils.websocket import Websocket
from utils.get_safest_path import get_safest_path
from utils.display_direction import display_direction, display_cross, reset_cross
from utils.floor_plan import get_floor_plan
from utils.event_loop import EventLoop
from utils.audio import Alarm
env = load_env()
# _thread.stack_size(2048)  # Set stack size to 2 KB (adjust as needed)

# Get environment variables
ssid = env.get("WIFI_SSID")
password = env.get("WIFI_PASSWORD")
floor_id = env.get("FLOOR_ID")
node_id = env.get("NODE_ID")
server_url = env.get("SERVER_URL")
audio_volume = float(env.get("AUDIO_VOLUME"))
gas_sensor_pin = int(env.get("GAS_SENSOR_PIN"))
gas_threshold = int(env.get("GAS_THRESHOLD"))

event_loop = EventLoop()

gas_sensor = Pin(gas_sensor_pin)

# Constants that can be changed from Serial monitor
# FLOOR_ID, NODE_ID, GAS_THRESHOLD, AIR_THRESHOLD


state_colors = {
  "safe": (2, 119, 189),
  "compromised": (255, 0, 0),
  "stuck": (255, 136, 0),
  "exit": (76, 175, 80)
}

floor_plan = {}
state = "safe"
detected_fire = False
updating_server = False
floor_name = ""
node_name = ""
created_thread = False
# Work on updating logic to use name instead of id

# Setup
wlan = connect_to_wifi(ssid, password)
# print(get_mac_address(wlan))

url = f"ws://{server_url}"
headers = {
  "Cookie": "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NzkxYTc3MjA4YzhiZDE1YTRlZjgzNzMiLCJyb2xlcyI6WyJ1c2VyIl0sImlhdCI6MTczNzc3ODE2MSwiZXhwIjoxNzM4MzgyOTYxfQ.j058GKHjJN_CR7eEWNtAozcrDOmzdjoNMZ-TSwUoCGw; Path=/; HttpOnly; Expires=Sat, 23 Nov 2024 06:08:07 GMT;",
}
subprotocols = ["graphql-transport-ws"]

print("Getting floor plan...")
response = get_floor_plan(floor_id, headers)

def on_message():
  global state, detected_fire, floor_plan, floor_name, node_name
  if "name" in floor_plan:
    floor_name = floor_plan.get("name")
  if "nodes" in floor_plan:
    for node in floor_plan.get("nodes"):
      if node.get("id") == node_id:
        node_name = node.get("name")
    print("Calculating safest path...")
    state, direction, detected_fire = get_safest_path(node_id, floor_plan)
    display_direction(direction, state_colors.get(state))
    floor_plan = {}

print("Got floor plan")
if response:
  response = json.loads(response)
  data = response.get("data", {})
  # Maybe a switch statement would be more intuitive
  if data.get("getFloorPlan"):
    floor_plan = data.get("getFloorPlan")

on_message()

ws = Websocket(url, headers, subprotocols=subprotocols)
ws.initialize()

fire_trigger_time = (int(time.time())) + 10

query = f"""
  subscription{{
    floorUpdate(id: \"{floor_id}\"){{
      name
      nodes {{
        id
        state
        isExit
        connections{{
          id
          name
          direction
        }}
        ui {{
          x
          y
        }}
      }}
    }}
  }}
"""
message = {
  "type": "subscribe",
  "payload": {
    "query": query
  }
}
ws.subscribe(message)


def check_for_response():
  print("Checking for response...")
  global floor_plan, ws
  if not ws:
    return
  response = ws.receive_message()
  if response:
    print("Message recieved from socket")
    try:
      response = json.loads(response)
    except:
      print("Error decoding response", response)
      response = {}
    if(response.get("payload", {}).get("data", {}).get("floorUpdate")):
      floor_plan = response.get("payload", {}).get("data", {}).get("floorUpdate")

def detect_fire():
  global node_id, updating_server, ws, fire_trigger_time, gas_threshold, gas_sensor, state
  if state != "compromised" and gas_sensor.value() >= gas_threshold:
  # if not updating_server and time.ticks_ms() / 1_000 > fire_trigger_time:
    # If fire detected, close the websocket, set node on fire, and open the
    # websocket again
    print("Fire detected!")
    updating_server = True
    # ws.s.close()

    query = f"""
      subscription{{
        nodeUpdate(id: \"{node_id}\")
      }}
    """
    message = {
      "type": "subscribe",
      "payload": {
        "query": query
      }
    }
    ws.subscribe(message)
    state = "compromised"


def blink_cross(color):
  next_execution = time.time()
  displaying_cross = False
  while True:
    if state == "compromised":
      # Blink the cross
      current_time = time.time()
      if displaying_cross:
        if current_time > next_execution:
          print("Cross reset!")
          reset_cross()
          displaying_cross = False
          next_execution = current_time + 0.5
      else:
        if current_time > next_execution:
          print("Cross displayed!")
          display_cross(color)
          displaying_cross = True
          next_execution = current_time + 0.5
    # Cleanup 
    elif displaying_cross:
      reset_cross()
    yield

def alarm_task(*args, **kwargs):
  alarm = Alarm(*args, **kwargs)
  alarm.stop_tone()
  playing_alarm = False
  play_alarm_gen = None
  # alarm.play_alarm(4)

  next_execution = time.time()
  while True:
    current_time = time.time()
    if playing_alarm and play_alarm_gen:
      try:
        next(play_alarm_gen)
      except StopIteration:
        print("Alarm stopped, waiting 0.8 seconds")
        playing_alarm = False
        play_alarm_gen = None
        next_execution = (time.time()) + 0.8
    elif current_time >= next_execution and detected_fire:
      playing_alarm = True
      play_alarm_gen = alarm.play_alarm(4)
    yield

"""
Needed a way to run the blinking lights and alarm in parallel without blocking
the thread with time.sleep
time.sleep blocks the thread and prevents other tasks from running makking
everything look janky
"""
def alert_floor(color, *args, **kwargs):
  cross_gen = blink_cross(color)
  alarm_gen = alarm_task(*args, **kwargs)

  while True:
    next(cross_gen)
    next(alarm_gen)

def create_thread():
  global created_thread
  retry_count = 5
  while retry_count > 0:
    try:
      _thread.start_new_thread(alert_floor, ((255, 0, 0), 2200, 0.12, audio_volume))
      break
    except Exception as e:
      print(f"Error: {e}")
    yield

event_loop.create_task(on_message)
event_loop.create_task(check_for_response)
# event_loop.add_task(create_thread)
event_loop.create_task(detect_fire)
# event_loop.add_task(blink_cross, (255, 0, 0))
# event_loop.add_task(alarm_task, 2200, 0.12, audio_volume)
# What if I keep it in the thread?????
try:
  _thread.start_new_thread(alert_floor, ((255, 0, 0), 2200, 0.12, audio_volume))
except Exception as e:
  print(f"Error: {e}")

event_loop.run_until_complete()
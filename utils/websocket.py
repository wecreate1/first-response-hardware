import socket
import os
import json
import random
from utils.ubinascii import b2a_base64

def generate_random_string(length=10):
  # Allowed characters: 0-9, A-Z, a-z
  characters = [chr(i) for i in range(48, 58)] + [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)]
  random_string = ''.join(random.choice(characters) for _ in range(length))
  return random_string

class Websocket():
  def __init__(self, url, headers=None, subprotocols=None):
    try:
      proto, dummy, host, path = url.split("/", 3)
    except ValueError:
      proto, dummy, host = url.split("/", 2)
      path = ""

    if proto == "ws:":
      port = 80
    elif proto == "wss:":
      import tls

      port = 443
    else:
      raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
      host, port = host.split(":", 1)
      port = int(port)

    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    ai = ai[0]

    self.s = socket.socket(ai[0], ai[1], ai[2])
    try:
      self.s.connect(ai[-1])
      self.s = self.s.makefile("rwb", buffering=False, newline="\r\n")
      if proto == "wss:":
        context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
        context.verify_mode = tls.CERT_NONE
        self.s = context.wrap_socket(self.s, server_hostname=host)


      sec_websocket_key = b2a_base64(os.urandom(16)).decode().strip()

      # Create the HTTP GET request message
      headers_list = [
        f"GET /{path} HTTP/1.1",
        f"Host: {host}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {sec_websocket_key}",
        "Sec-WebSocket-Version: 13"
      ]

      # Add any custom headers
      if headers:
        for key, value in headers.items():
          headers_list.append(f"{key}: {value}")

      # Add the subprotocols header if specified
      if subprotocols:
        headers_list.append(f"Sec-WebSocket-Protocol: {', '.join(subprotocols)}")

      handshake = "\r\n".join(headers_list) + "\r\n\r\n"

      # print(handshake)
      self.s.write(handshake.encode())
      # Read the response from the server
      self.read()
      # print("Complete data received:", self.read())
    except OSError:
      self.s.close()
      raise
  
  def initialize(self):
    # self.send_ping()
    # self.send_pong()
    message = {
      "type": "connection_init"
    }
    message = json.dumps(message).encode("utf-8")
    self.send_message(message)
    response = self.receive_message()
    # print("Message from server:", response)
  
  def read(self):
    str = b""
    while True:
      l = self.s.readline()
      if not l or l == b"\r\n":
        break
      str += l
    return str
  
  def send_ping(self):
    # Create a WebSocket ping frame with a mask
    ping_frame = bytearray([0x89])  # 0x89 (FIN + ping opcode)

    # Ping frame has no payload, so payload length is zero
    payload_length = 0
    ping_frame.append(0x80 | payload_length)  # Mask bit set and length 0

    # Generate a 4-byte masking key
    masking_key = os.urandom(4)
    ping_frame.extend(masking_key)  # Append the masking key to the frame

    # Send the masked ping frame
    self.s.write(ping_frame)
  
  def send_pong(self):
    # Create a WebSocket pong frame with a mask
    pong_frame = bytearray([0x8A])  # 0x8A (FIN + pong opcode)

    # Pong frame has no payload, so payload length is zero
    payload_length = 0
    pong_frame.append(0x80 | payload_length)  # Mask bit set and length 0

    # Generate a 4-byte masking key
    masking_key = os.urandom(4)
    pong_frame.extend(masking_key)  # Append the masking key to the frame

    # Send the masked pong frame
    self.s.write(pong_frame)
  
  def send_message(self, message):
    # Create a WebSocket frame for a text message
    frame = bytearray()

    # Set FIN bit and text frame opcode
    frame.append(0x81)  # 0x80 (FIN) | 0x1 (text)

    # Determine the payload length and set accordingly
    payload_length = len(message)
    if payload_length <= 125:
      frame.append(0x80 | payload_length)  # 0x80 indicates masking
    elif payload_length <= 65535:
      frame.append(0xFE)
      frame.extend(payload_length.to_bytes(2, 'big'))
    else:
      frame.append(0xFF)
      frame.extend(payload_length.to_bytes(8, 'big'))

    # Generate a masking key and mask the payload
    masking_key = os.urandom(4)
    frame.extend(masking_key)

    # Apply mask to the payload
    masked_payload = bytearray([message[i] ^ masking_key[i % 4] for i in range(payload_length)])
    frame.extend(masked_payload)

    # Send the framed message
    self.s.write(frame)
    print("sent")
  
  def receive_message(self):
    # Read the first byte for FIN and opcode
    # self.send_ping()
    first_byte = self.s.read(1)
    if not first_byte:
      return None
    fin_and_opcode = ord(first_byte)
    
    # Extract the opcode
    opcode = fin_and_opcode & 0x0F
    if(opcode == 0x0):
      return None
    # 0x1 = Text frame, 0x2 = Binary frame, 0x9 = Ping, 0xA = Pong
    # send_pong(socket)
    if opcode == 0x8:
      print("Received close frame;")
      # Respond to close with close frame
      # close_frame = bytearray([0x88, 0x00])  # 0x88 is a close frame with no payload
      # socket.write(close_frame)
      return None
    elif opcode == 0x9:
      print("Received ping frame; responding with pong")
      # Respond to ping with pong
      # pong_frame = bytearray([0x8A, 0x00])  # 0x8A is a pong frame with no payload
      # socket.write(pong_frame)
      self.send_pong()
      return None
    elif opcode == 0xA:
      print("Received pong frame")
      return None

    # Read the payload length
    second_byte = ord(self.s.read(1))
    masked = (second_byte & 0x80) != 0
    payload_length = second_byte & 0x7F

    if payload_length == 126:
      payload_length = int.from_bytes(self.s.read(2), 'big')
    elif payload_length == 127:
      payload_length = int.from_bytes(self.s.read(8), 'big')

    # Read the masking key if present
    if masked:
      masking_key = self.s.read(4)
    else:
      masking_key = None

    # Read the payload data
    payload = self.s.read(payload_length)
    if masked:
      payload = bytearray([payload[i] ^ masking_key[i % 4] for i in range(payload_length)])

    # self.send_pong()
    # Decode only if it's a text frame
    if opcode == 0x1:  # Text frame
      return payload.decode('utf-8')
    else:  # Other opcodes like Binary frame
      return payload  # Return as raw data without decoding
  
  def subscribe(self, json_message):
    id = generate_random_string()
    print(id, str(id))
    json_message["id"] = str(id)
    message = json.dumps(json_message).encode("utf-8")

    self.send_message(message)
    self.send_pong()
  
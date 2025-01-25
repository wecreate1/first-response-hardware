import time
from machine import Pin, PWM
from utils.load_env import load_env

env = load_env()

class Alarm:
  def __init__(self, frequency, duration, tone_volume):
    audio_pin = int(env.get("AUDIO_PIN"))
    self.audio = PWM(Pin(audio_pin))
    self.audio.duty_u16(0)
    self.frequency = frequency
    self.duration = duration
    self.tone_volume = tone_volume
    print("Alarm initialized")
  
  def play_tone(self):
    if self.frequency == 0:
      self.audio.duty_u16(0)
    else:
      self.audio.freq(self.frequency)
      print("playing tone")
      self.audio.duty_u16(int(self.tone_volume * 65535))  # 50% duty cycle
  
  def stop_tone(self):
    self.audio.duty_u16(0)

  # Create a generator to play the alarm
  """
    Although I moved this function to a different thread, it still fights for
    time with the cross blinking function

    To prevent that, I tore the function apart and yielded at every moment where
    this function does not need to run
    A lot like how JavaScript event loops work

    It's made the alarm/crossing tasks run in parallel and less janky to look at/hear
  """
  def play_alarm(self, iterations):
    playing = True
    self.play_tone()
    next_execution = (time.time()) + self.duration
    print("Alarm started, for " + str(self.duration) + " seconds")
    # Play the alarm, make sure not to stop until the alarm does
    played_count = 1
    while played_count < iterations:
      current_time = time.time()
      if current_time >= next_execution:
        if playing:
          print("Alarm stopped, waiting 0.1 seconds")
          self.stop_tone()
          playing = False
          next_execution = (time.time()) + 0.1
        else:
          print("Alarm started, for " + str(self.duration) + " seconds")
          self.play_tone()
          playing = True
          played_count += 1
          next_execution = (time.time()) + self.duration
      yield
    
    # If beep is still on
    if playing:
      current_time = time.time()
      while current_time < next_execution:
        current_time = time.time()
        yield
      print("Final Alarm stopped")
      self.stop_tone()
      playing = False
      yield


import demo

class Pin:
    def __init__(self, pin):
        self._pin = pin
    def value(self):
        return 0

class PWM:
    def __init__(self, pin):
        self._pin = pin._pin
        self._duty = 0
        self._freq = 0
    
    def duty_u16(self, duty):
        if self._pin == demo.audio_pin:
            demo.alarm_duty = duty
        demo.update()

    def freq(self, freq):
        if self._pin == demo.audio_pin:
            demo.alarm_freq = freq
        demo.update()
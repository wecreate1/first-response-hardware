import demo

class NeoPixel:
    def __init__(self, pin, num_leds):
        self._pin = pin._pin
        # self._leds = [(0,0,0) for _ in range(num_leds)]

    def __setitem__(self, idx, value):
        # self._leds[idx] = value
        if self._pin == demo.neo_dir_pin:
            demo.np_dir[idx] = value
        elif self._pin == demo.neo_cross_pin:
            demo.np_cross[idx] = value
        demo.dirty = True

    def write(self):
        if demo.dirty:
            demo.update()
            demo.dirty = False
    
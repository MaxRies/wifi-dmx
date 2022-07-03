import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger('LightGroup')

class Light:
    def __init__(self, channel):
        self._r = 0
        self._g = 0
        self._b = 0
        self._channel = channel   # TODO Add channels
        self._x = 0.0
        self._y = 0.0
        self._dimmer = 1.00
    
    def __repr__(self) -> str:
        return (f"{self._channel}: ({self.r}, {self.g}, {self.b})")

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, new_r):
        new_r = int(new_r)
        if new_r < 0:
            new_r = 0
        elif new_r > 255:
            new_r = 255
        self._r = new_r

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, new_g):
        new_g = int(new_g)
        if new_g < 0:
            new_g = 0
        elif new_g > 255:
            new_g = 255
        self._g = new_g

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, new_b):
        new_b = int(new_b)
        if new_b < 0:
            new_b = 0
        elif new_b > 255:
            new_b = 255
        self._b = new_b

    @property
    def color(self):
        return (self.r, self.g, self.b)

    @color.setter
    def color(self, new_color):
        logger.info(f"Received {new_color}")
        if type(new_color) is list or type(new_color) is tuple:
            if len(new_color) == 3:
                self.r = new_color[0]
                self.g = new_color[1]
                self.b = new_color[2]
                logger.info(f"Set {self._channel} to {r},{g},{b}")
            else:
                raise ValueError("Wrong color object passed. To little values.")
        elif type(new_color) is str:
            #TODO Add dictionary of light names
            pass

    @property
    def dimmer(self):
        return self._dimmer

    @dimmer.setter
    def dimmer(self, new_dimmer):
        if new_dimmer > 1.0:
            new_dimmer = 1.0
        elif new_dimmer < 0.0:
            new_dimmer = 0.0
        self._dimmer = new_dimmer

    def dimmed_values(self):
        value_r = int(self._r * self._dimmer)
        value_g = int(self._g * self._dimmer)
        value_b = int(self._b * self._dimmer)
        return (value_r, value_g, value_b)

    @property
    def float_values(self):
        value_r = (self.r * self._dimmer) / 255.0
        value_g = (self.g * self._dimmer) / 255.0
        value_b = (self.b * self._dimmer) / 255.0
        return (value_r, value_g, value_b)


    @float_values.setter
    def float_values(self, new_vals):
        assert len(new_vals) == 3
        self.r = int(new_vals[0] * 255.0)
        self.g = int(new_vals[1] * 255.0)
        self.b = int(new_vals[2] * 255.0)

    @property
    def channel(self):
        return self._channel


class DMXLight(Light):
    def __init__(self, channel, width):
        super().__init__()
        self._channel = channel
        self._width = width

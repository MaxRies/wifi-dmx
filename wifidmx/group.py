from cmath import pi
from light import Light
from plot_lights import draw_lights

from stupidArtnet import StupidArtnet

from time import time, sleep
from math import sin
import random
import logging
from enum import Enum

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger('LightGroup')

### GLOBALS ####


### ARTNET RELATED ####
# THESE ARE MOST LIKELY THE VALUES YOU WILL BE NEEDING
target_ip = '2.0.0.1'		# typically in 2.x or 10.x range
universe = 0 										# see docs
number_of_lamps = 5
channels_per_lamp = 6
packet_size = number_of_lamps * channels_per_lamp							# it is not necessary to send whole universe

# CREATING A STUPID ARTNET OBJECT
# SETUP NEEDS A FEW ELEMENTS
# TARGET_IP   = DEFAULT 127.0.0.1
# UNIVERSE    = DEFAULT 0
# PACKET_SIZE = DEFAULT 512
# FRAME_RATE  = DEFAULT 30
# ISBROADCAST = DEFAULT FALSE
dmx_net = StupidArtnet(target_ip, universe, packet_size, 30, True, True)
dmx_packet = bytearray(packet_size)		# create packet for Artnet
for i in range(packet_size):			# fill packet with sequential values
    dmx_packet[i] = (i % 256)

# ... AND SET IT TO STUPID ARTNET
dmx_net.set(dmx_packet)						# only on changes



###### LIGHT RELATED ########
FPS = 30.0


def print_light(values):
    for val in values:
        print(f"{fg(val)}●")


def render_dmx(lights):
    for index, light in enumerate(lights):
        # channel_begin = index * channels_per_lamp + 1

        channel_begin = light.channel
        
        dmx_net.set_single_value(channel_begin, 241)
        dmx_net.set_single_value(channel_begin+1, light.r)
        dmx_net.set_single_value(channel_begin + 2, light.g)
        dmx_net.set_single_value(channel_begin + 3, light.b)
        dmx_net.set_single_value(channel_begin + 4, 0) # White
        dmx_net.set_single_value(channel_begin + 5, 0) # Mode

        print(light)
        
    dmx_net.show()


class Ball():
    def __init__(self, color, speed, num_lights):
        # Idea: A ball is a small effect that travels all the lights and then disappears.
        # It should travel fairly quick (2 seconds max.)
        # So if speed is low it takes 2 seconds for all lights, and if speed is 1, it takes just Num_lights_frames to complete
        # Step is called every loop, but we only step one light ahead if it's time.

        self._position = 0
        self._color = color
        self._speed = speed
        now = time()
        self._start = now
        self._number_of_lights = num_lights

        self._step_interval = ((2.0 - (1/30.0)) / (-1.0) * self._speed + 2.0) / self._number_of_lights
        self._last_step = now


    def step(self):
        now = time()
        if now > self._last_step + self._step_interval:
            self._position += 1
            self._last_step = now


class Pattern(Enum):
    BREATHE = 0
    FULL_FADE = 1
    BEAT_CIRCLE = 2
    STROBE = 3


class LightGroup:
    colors = {
        "white": (255, 255, 255),
        "blue": (0, 0, 255),
        "purple": (128, 0, 128),
        "rosybrown": (188, 143, 143),
        "darkorchid": (153, 50, 204),
        "tomato": (255, 99, 71),
        "red": (255, 0, 0),
        "sienna": (160,	82,	45),
        "fuchsia": 	(255, 0, 255),
        "turqouise": (64, 224, 208)
    }

    def __init__(self) -> None:
        # FIXME for production!
        self.auto_animation = True
        self.auto_beat = 0.5    # 2 bps = 120 bpm

        self._lights = None
        self._brightness = []

        self._fg_color = (255, 0, 0)
        self._bg_color = (0, 0, 80)

        self._render_function = render_dmx

        # effect timers
        self._animation_start = 0.0

        self._beat_interval = 0.5
        self._last_beat = 0.0
        self._beat_used = False # True wenn ein Beat reinkam, aber noch nicht verwendet wurde

        # RENDERING
        self._last_render = 0.0
    
    def __repr__(self) -> str:
        repr = ""
        for light in self._lights:
            repr += str(light)
            repr += "\n"
        return repr


    def set_render_function(self, function):
        """
        Render function must accept array of light objects and display them somehow.
        """
        self._render_function = function

    def render(self):
        self._render_function(self._lights)

    def reset_timers(self):
        self._last_strobe_on = time()
        self._last_strobe_off = time()
        self._animation_start = time()

    def add_light(self, light: Light):
        if self._lights is None:
            self._lights = [light]
        else:
            self._lights.append(light)

    def set_lights_color(self, color):
        for light in self._lights:
            light.color = color
    
    def set_lights_dimmer(self, dimmer):
        """
        Dimmer Value: [0.0, 1.0]
        """
        if dimmer < 0:
            dimmer = 0.0
        elif dimmer > 1:
            dimmer = 1.0

        for light in self._lights:
            light.dimmer = dimmer

    """
    ###############################
    Pattern Functions - BACKGROUND
    ###############################
    """


    def strobe(self, frequency):
        """
        #FIXME: Do this via DMX Light strobe function
        """
        if time() - self._last_strobe_on > 1/frequency:
            self._last_strobe_on = time()
            if self._strobe_on:
                self.set_lights_dimmer(0.0)
                self._strobe_on = False
            else:
                self.set_lights_dimmer(1.0)
                self._strobe_on = True

    def rotate_forward(self):
        self._rotation_lead += 1
        self._rotation_lead = self._rotation_lead % len(self._lights)

    def rotate_lights(self, frequency):
        self._lights[self._rotation_lead].dimmer = 1.0
        self.rotate_forward()

    def fade(self, factor = 0.8):
        for light in self._lights:
            light.dimmer = light.dimmer * factor

    def fill(self, color):
        for light in self._lights:
            light.color = color

    def beat_circle(self, per_bar=False):
        # Pattern: One full light circle for each beat
        time_for_lap = self._beat_interval

        if per_bar:
            time_for_lap *= 4   # Take a whole bar for the time

        lights_per_lap = len(self._lights)

        animation_fraction = (time() - self._animation_start) / time_for_lap

        if animation_fraction > 1.0:
            logger.info("Animation_fraction bigger than 1.0")
            self.reset_timers()
        else:
            self.fade()
            current_position = (int(lights_per_lap * animation_fraction) % 16)
            logger.info(f"Animation_fraction: {animation_fraction} Position: {current_position}")
            self._lights[current_position].color = self._fg_color


    def full_fade(self, beat_now):
        # Pattern: Light up all the lights on the beat, in between fade
        if beat_now is True:
            self.fill(self._fg_color)
            self.set_lights_dimmer(1.0)
            logger.debug("FULL FADE FILL")
        else:
            self.fade(0.8)

    def breathe(self):
        # Pattern: Just breathe steadily
        now = time()
        breathe_time = 3

        dimmer_value = 0.5 * sin((2*pi / breathe_time) * (now - self._animation_start)) + 0.5 

        self.fill(self._fg_color)
        self.set_lights_dimmer(dimmer_value)


    """
    #####################################
    PATTERN FUNCTIONS
    FOREGROUND
    #####################################
    """

    def ball(self):
        if not self._beat_used:
            # Spawn a new ball
            pass

    def beat(self):
        self._beat_interval = self._last_beat - time()
        self._last_beat = time()
        self._beat_used = False


    def check_for_beat(self):
        # Check UDP Socket for beat


        if self.auto_animation:
            if time() - self._last_beat > self.auto_beat:
                self._last_beat = time()
                logger.info("BEAT!")
                return True
            else:
                return False
        else:
            if self._beat_used == False:
                return True
            else:
                return False

    def loop(self):
        # This function is called once per Frame.
        # It calls the appropriate functions to manipulate the light state and renders them.
        now = time()
        # Check if we have a beat
        self._beat_now = self.check_for_beat()


        if self._animation == Pattern.FULL_FADE:
            self.full_fade()
        elif self._animation == Pattern.BEAT_CIRCLE:
            self.beat_circle()
        elif self._animation == Pattern.STROBE:
            pass
        elif self._animation == Pattern.BREATHE:
            self.breathe()

        # Only render with 30 FPS
        if now - self._last_render > 1/FPS:
            self._render_function(self._lights)
            self._last_render = now

        self._beat_now = False
        self._beat_used = True

    
    @property
    def pattern(self):
        return self._animation

    @pattern.setter
    def pattern(self, new_pattern):
            self._animation = Pattern(new_pattern)
            logger.info(f"Set pattern to {self._animation}")

        

def sleep(vals):
    from time import sleep
    sleep(0.05)

def rotate_colors(position):
    light_colors = [(i/16.0, 0.0, 1.0-i/16.0) for i in range(0,16) ]
    
    return [light_colors[(i + position) % 16] for i in range (0,16)]


if __name__ == "__main__":
    group = LightGroup()
    for i in range (0,16):
        light = Light(i * channels_per_lamp + 1)
        group.add_light(light)

    logger.info(group)
    group.pattern = Pattern.BEAT_CIRCLE
    group.set_render_function(sleep)

    while True:
        try:
            group.loop()
        except KeyboardInterrupt:
            break
    
    """
    for i in range(0,16):
        try:
            light_values = rotate_colors(i)
            draw_lights(light_values)
        except KeyboardInterrupt:
            break
    
    for i in range (0, number_of_lamps):
        light = Light()
        light.color = (255,255,0)
        group.add_light(light)

    while True:
        try:
            group.rotate_lights(10)
            group.render()
            sleep(0.01)
            group.fade()
            group.render()
            sleep(0.01)
            group.fade()
            group.render()
            sleep(0.01)
            group.fade()
            group.render()
            sleep(0.01)
        except KeyboardInterrupt:
            break
    """

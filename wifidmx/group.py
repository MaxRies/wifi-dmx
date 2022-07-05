from cmath import pi
from light import Light
# from plot_lights import draw_lights

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
logger.setLevel(logging.INFO)
### GLOBALS ####

### ARTNET RELATED ####
# THESE ARE MOST LIKELY THE VALUES YOU WILL BE NEEDING
target_ip = '192.168.0.244'		# typically in 2.x or 10.x range
universe = 0 										# see docs
number_of_lamps = 16
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


logger.info(f"DMX IP: {target_ip}")
logger.info(f"Number of lamps: {number_of_lamps}")
logger.info(f"FPS: {FPS}")


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
    SOLID = 0
    BREATHE = 1
    FULL_FADE = 2
    BEAT_BLINK = 3
    BEAT_CIRCLE = 4
    STROBE = 5
    BREATHE_FAST = 6


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
        self.auto_beat_interval = 0.5    # 2 bps = 120 bpm

        self._lights = None
        
        self._global_dimmer = 1.0
        self._animation_dimmer = 1.0
        self._speed=1.0

        self._fg_color = (255, 0, 0)
        self._bg_color = (0, 0, 80)

        self._render_function = self.render_dmx

        self._strobe_on = False

        self._old_pattern = Pattern.SOLID
        self._strobe_start = 0.0
        self._strobe_end = 0.0
        self._short_strobe = False

        # effect timers
        self._animation_start = 0.0
        self._pattern_start = 0.0

        self._beat_circle_start = 0.0
        self._breathe_start = 0.0

        self._beat_interval = 0.5
        self._last_beat = 0.0
        self._beat_used = False # True wenn ein Beat reinkam, aber noch nicht verwendet wurde

        # RENDERING
        self._last_render = 0.0

        # Initial animation:
        self._animation = 0
    
    def __repr__(self) -> str:
        repr = ""
        for light in self._lights:
            repr += str(light)
            repr += "\n"
        return repr

    def render_dmx(self, lights, dimmer):
        for index, light in enumerate(lights):
            # channel_begin = index * channels_per_lamp + 1

            channel_begin = light.channel

            if self._strobe_on:
                dmx_net.set_single_value(channel_begin, 239)
                self._animation_dimmer = 1.0
                self._dimmer = 1.0
                for light in lights:
                    light.dimmer = 1.0
                logger.debug("Strobe on")
            else:
                dmx_net.set_single_value(channel_begin, 241)
                logger.debug("Strobe off")

            r,g,b = light.dimmed_values()

            global_dimmed_r = int(r * dimmer * self._animation_dimmer)
            global_dimmed_g = int(g * dimmer * self._animation_dimmer)
            global_dimmed_b = int(b * dimmer * self._animation_dimmer)
            logger.debug("DIMMED R: {} G: {} B: {}".format(global_dimmed_r, global_dimmed_g, global_dimmed_b))

            dmx_net.set_single_value(channel_begin+1, global_dimmed_r)
            dmx_net.set_single_value(channel_begin + 2, global_dimmed_g)
            dmx_net.set_single_value(channel_begin + 3, global_dimmed_b)
            dmx_net.set_single_value(channel_begin + 4, light._white) # White
            dmx_net.set_single_value(channel_begin + 5, light._auto) # Mode
            logger.debug(light)
        
        
        logger.debug(dmx_packet)
        dmx_net.show()


    def set_render_function(self, function):
        """
        Render function must accept array of light objects and display them somehow.
        """
        self._render_function = function

    def render(self):
        self._render_function(self._lights, self._dimmer)

    def reset_timers(self):
        now = time()
        self._animation_start = now

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
        try:
            dimmer = float(dimmer)
        except ValueError:
            logger.warn("Passed invalid input to set_lights_dimmer: {}".format(dimmer))
        if dimmer < 0:
            dimmer = 0.0
        elif dimmer > 1:
            dimmer = 1.0

        for light in self._lights:
            light.dimmer = dimmer


    def set_global_dimmer(self, dimmer):
        """
        Dimmer Value: [0.0, 1.0]
        """
        try:
            dimmer = float(dimmer)
        except ValueError:
            logger.warn("Passed invalid input to set_lights_dimmer: {}".format(dimmer))
        if dimmer < 0:
            dimmer = 0.0
        elif dimmer > 1:
            dimmer = 1.0

        self.dimmer = dimmer
        logger.info(f"Set global Dimmer to {dimmer}")


    def set_pattern(self, new_pattern):
        """
        Expected Input: 0 -> len(Pattern)
        """
        if type(new_pattern) == Pattern:
            self.pattern = new_pattern
        else:
            try:
                new_pattern = int(new_pattern)
            except ValueError:
                logger.warn("Passed invalid input to set_pattern: {}".format(new_pattern))
                logger.warn(type(new_pattern))

            if new_pattern < 0:
                new_pattern = 0
            elif new_pattern >= len(Pattern):
                new_pattern = len(Pattern) - 1
            try:
                self.pattern = Pattern(new_pattern)
            except ValueError:
                logger.warn("Passed invalid input to set_pattern: {}".format(new_pattern))
                logger.warn(type(new_pattern))


    def set_speed(self, new_speed):
        """
        Speed Value: [0.0, 1.0]
        """
        try:
            new_speed = float(new_speed)
        except ValueError:
             logger.warn("Passed invalid input to set_speed: {}".format(new_speed))

        if new_speed < 0:
            new_speed = 0.0
        elif new_speed > 1:
            new_speed = 1.0
        
        self._speed = new_speed


    """
    ###############################
    Pattern Functions - BACKGROUND
    ###############################
    """


    def strobe(self, frequency):
        """
        #FIXME: Do this via DMX Light strobe function
        """
        for light in self._lights:
            light.strobe = True


    def lamps_fade(self, factor = 0.8):
        # self._animation_dimmer = self._animation_dimmer * factor
        for light in self._lights:
            light.dimmer = light.dimmer * factor

    def fade(self, factor = 0.8):
        self._animation_dimmer = self._animation_dimmer * factor
        
    def fill(self, color):
        for light in self._lights:
            light.color = color
            light.dimmer = 1.0

    def beat_circle(self, per_bar=False):
        # Pattern: One full light circle for each beat
        time_for_lap = self._beat_interval

        if per_bar:
            time_for_lap *= 4   # Take a whole bar for the time

        lights_per_lap = len(self._lights)

        animation_fraction = (time() - self._beat_circle_start) / time_for_lap

        if animation_fraction > 1.0:
            logger.info("Animation_fraction bigger than 1.0")
            self._beat_circle_start = time()
            self._pattern_start = time()
            self._animation_dimmer = 1.0
        else:
            self.lamps_fade()
            current_position = (int(lights_per_lap * animation_fraction) % lights_per_lap)
            logger.info(f"Animation_fraction: {animation_fraction} Position: {current_position}")
            self._lights[current_position].color = self._fg_color
            self._lights[current_position].dimmer = 1.0
            # This does not work. all lights get dimmed by animation dimmer.


    def full_fade(self, beat_now):
        # Pattern: Light up all the lights on the beat, in between fade
        if beat_now is True:
            self.fill(self._fg_color)
            self._animation_dimmer = 1.0
            logger.info("FULL FADE FILL")
        else:
            self.fade(0.8)

    def breathe(self):
        # Pattern: Just breathe steadily
        now = time()
        breathe_time = 4 * self._beat_interval

        dimmer_value = 0.5 * sin((2*pi / breathe_time) * (now - self._breathe_start)) + 0.5 

        self.fill(self._fg_color)
        self._animation_dimmer = dimmer_value

    def breathe_fast(self):
        # Pattern: Just breathe steadily
        now = time()
        breathe_time = self._beat_interval

        dimmer_value = 0.5 * sin((2*pi / breathe_time) * (now - self._breathe_start)) + 0.5 

        self.fill(self._fg_color)
        self._animation_dimmer = dimmer_value

    def solid(self):
        self.fill(self._fg_color)
        self.set_lights_dimmer(self._dimmer)
        self._animation_dimmer = 1.0


    """
    #####################################
    PATTERN FUNCTIONS
    FOREGROUND
    #####################################
    """

    def beat_blink(self):
        if self._beat_used == False:
            for light in self._lights:
                light.color = self._fg_color
            self._beat_used = True
        else:
            for light in self._lights:
                light.color = self._bg_color


    def ball(self):
        if not self._beat_used:
            # Spawn a new ball
            pass
    
    def short_strobe(self, length=0.5):
        now = time()
        self._old_pattern = self.pattern
        self._strobe_start = now
        self._strobe_end = now + length
        self._short_strobe = True

    def beat(self):
        logger.info("BEAT!")
        self._beat_interval = self._last_beat - time()
        self._last_beat = time()
        self._beat_used = False

    
    def christophbeat(self):
        if self.auto_animation:
            pass
        else:
            self.beat()
            logger.info("Christophbeat!")


    def check_for_beat(self):
        # TODO
        # Check UDP Socket for beat


        if self.auto_animation:
            if time() - self._last_beat > self.auto_beat_interval:
                self.beat()
                return True
            else:
                return False
        else:
            if self._beat_used is False:
                return True
            else:
                return False
        
    def loop(self):
        # This function is called once per Frame.
        # It calls the appropriate functions to manipulate the light state and renders them.
        now = time()
        # Check if we have a beat
        if now < self._strobe_end:
            self._animation = Pattern.STROBE
        else:
            if self._short_strobe:
                if self._old_pattern != Pattern.STROBE:
                    self._animation = self._old_pattern
                else:
                    self._animation = Pattern.SOLID
                self._short_strobe = False

        if now - self._last_render > 1/FPS:
            self._beat_now = self.check_for_beat()

            if self._animation == Pattern.FULL_FADE:
                self._strobe_on = False
                self.full_fade(self._beat_now)
            elif self._animation == Pattern.BEAT_CIRCLE:
                self._strobe_on = False
                self.beat_circle(per_bar=True)
            elif self._animation == Pattern.STROBE:
                for light in self._lights:
                    light.color = self._fg_color
                self._strobe_on = True
            elif self._animation == Pattern.BREATHE:
                self._strobe_on = False
                self.breathe()
            elif self._animation == Pattern.BREATHE:
                self._strobe_on = False
                self.breathe_fast()
            elif self._animation == Pattern.SOLID:
                self._strobe_on = False
                self.solid()
            elif self._animation == Pattern.BEAT_BLINK:
                self._strobe_on = False
                self.beat_blink()

            # Only render with 30 FPS
            self.render()
            self._last_render = now

            self._beat_now = False
            self._beat_used = True

    
    @property
    def pattern(self):
        return self._animation

    @pattern.setter
    def pattern(self, new_pattern):
            self._animation = Pattern(new_pattern)
            self._pattern_start = time()
            self._breathe_start = time()
            self._beat_circle_start = time()
            self._animation_dimmer = 1.0
            logger.info(f"Set pattern to {self._animation}")


    @property
    def dimmer(self):
        return self._dimmer

    @dimmer.setter
    def dimmer(self, new_value):
        if new_value < 0:
            new_value = 0
        elif new_value > 1:
            new_value = 1
        
        self._dimmer= new_value
        logger.info("Set Lightgroup Dimmer to {}".format(new_value))


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


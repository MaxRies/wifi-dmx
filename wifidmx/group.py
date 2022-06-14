from light import Light
from plot_lights import draw_lights

from stupidArtnet import StupidArtnet

from time import time, sleep
from math import sin
import random


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
FPS = 30


def print_light(values):
    for val in values:
        print(f"{fg(val)}●")

"""
def init_draw():
    draw_lights.ax, draw_lights.fig = plt.subplots()
    light_colors = [(i/16.0, 0.0, 1.0-i/16.0) for i in range(0,16) ]
    plt.scatter(light_positions_x, light_positions_y, c=light_colors, s=light_size)
    plt.draw()
    plt.pause(1)

def draw_lights(values):
    plt.scatter(light_positions_x, light_positions_y, c=values, s=light_size)
    plt.draw()
    plt.pause(0.5)
"""

def render_dmx(lights):
    for index, light in enumerate(lights):
        channel_begin = index * channels_per_lamp + 1
        
        dmx_net.set_single_value(channel_begin, 241)
        dmx_net.set_single_value(channel_begin+1, light.r)
        dmx_net.set_single_value(channel_begin + 2, light.g)
        dmx_net.set_single_value(channel_begin + 3, light.b)
        dmx_net.set_single_value(channel_begin + 4, 0) # White
        dmx_net.set_single_value(channel_begin + 5, 0) # Mode
        print(light)
    dmx_net.show()


class LightGroup:
    def __init__(self) -> None:
        self._lights = None
        self._brightness = []

        self._render_function = render_dmx

        # effect timers
        self._last_strobe_on = 0
        self._last_strobe_off = 0

        self._last_rotation = 0
        self._rotation_lead = 0

        # effect state
        self._strobe_on = False

        self._beat_interval = 0.5
        self._last_beat = 0.0
    
    def __repr__(self) -> str:
        repr = ""
        for light in self._lights:
            repr += str(light)
            repr += "\n"
        return repr


    def set_render_funcion(self, function):
        """
        Render function must accept array of light objects and display them somehow.
        """
        self._render_function = function

    def reset_timers(self):
        self._last_strobe_on = time()
        self._last_strobe_off = time()

    def add_light(self, light: Light):
        if self._lights is None:
            self._lights = [light]
        else:
            self._lights.append(light)

    def render(self):
        self._render_function(self._lights)

    def set_lights_color(self, color):
        for light in self._lights:
            light.color = color
    
    def set_lights_dimmer(self, dimmer):
        for light in self._lights:
            light.dimmer = dimmer

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

    def fade(self):
        for light in self._lights:
            light.dimmer = light.dimmer * 0.8

    



    
        
def rotate_colors(position):
    light_colors = [(i/16.0, 0.0, 1.0-i/16.0) for i in range(0,16) ]
    
    return [light_colors[(i + position) % 16] for i in range (0,16)]


if __name__ == "__main__":
    group = LightGroup()
    for i in range (0,16):
        light = Light(i * channels_per_lamp + 1)
        group.add_light(light)
    print(group)
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

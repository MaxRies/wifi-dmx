from stupidArtnet import StupidArtnet
import time
import random

from wifidmx.wifidmx.group import LightGroup

# THESE ARE MOST LIKELY THE VALUES YOU WILL BE NEEDING
target_ip = '255.255.255.255'		# typically in 2.x or 10.x range
universe = 0 										# see docs
packet_size = 100								# it is not necessary to send whole universe

# CREATING A STUPID ARTNET OBJECT
# SETUP NEEDS A FEW ELEMENTS
# TARGET_IP   = DEFAULT 127.0.0.1
# UNIVERSE    = DEFAULT 0
# PACKET_SIZE = DEFAULT 512
# FRAME_RATE  = DEFAULT 30
# ISBROADCAST = DEFAULT FALSE
a = StupidArtnet(target_ip, universe, packet_size, 30, True, True)



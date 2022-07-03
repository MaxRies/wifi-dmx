import paho.mqtt.client as mqtt

import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("controller")

MAXIMUM_MQTT_INT_VALUE = 65.536
BASE_TOPIC = "dmxlights"

MQTT_CONNECTED = False
MQTT_BROKEN = False

"""
Outline:
[ ] Connection Handling
[ ] Error Handling (Reconnect after disconnect!)
[ ] Make Topics configurable
[ ] Topics:
    - ColorFG
    - ColorBG
    - ColorMix
    - Pattern
    - Speed
    - AutoMove yes no
    - 
[ ] Beat Detection
    - UDP Socket, shared
"""

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
        "turqouise": (64, 224, 208),
        "black": (0,0,0)
    }

def string_to_color(colorstring: str):
    """
    Returns Tuple (R, g, b) or None
    """
    # let's see if the value is in the dict
    if colorstring.lower() in colors.keys():
        return colors[colorstring.lower()]
    else:
        # check if we have a tuple as string
        pass


def msg_to_color(msg):
    """
    Return Tuple (rgb) or none
    """
    logger.info(f"Received {msg.payload} as a color")
    list_of_colors = list(colors.items())
    # Check if color is a name or a number:
    try:
        picked_number = int(msg.payload)
        # we have a number
        color_index = int((picked_number / MAXIMUM_MQTT_INT_VALUE) * len(list_of_colors))
        color_name, values = list_of_colors[color_index]
        logger.info(f"color: {color_name}\tvalues:{values}")
    except ValueError:
        # check if name is in dict:
        # we have a string in a dict, hopefully
        values = string_to_color(msg.payload)
        return values



def handle_color_fg(msg):
    
    pass

def handle_color_bg(msg):
    pass



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("127.0.0.1", 1883, 60)
client.reconnect_delay_set(min_delay=1, max_delay=120)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
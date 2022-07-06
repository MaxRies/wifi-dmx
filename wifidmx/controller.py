import paho.mqtt.client as mqtt
import logging
from time import sleep

import communicator as comm

from light import Light
from group import LightGroup, Pattern

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("controller")

MAXIMUM_MQTT_INT_VALUE = 65536.0
BASE_TOPIC = "dmxlights"

DIMM_ST = "Dimm"
SPEED_ST = "Speed"
COLOR_ST = "Color"
PATTERN_ST = "Pattern"
FG_COLOR_ST = "fgColor"
BG_COLOR_ST = "bgColor"
AUTO_ST = "AutomaticBPM"
SHORT_STROBE = "shortStrobe"
STROBE_COLOR = "strobeColor"
FG_COLOR_STRING = "fgColorString"
BG_COLOR_STRING = "bgColorString"
STROBE_COLOR_STRING = "strobeColorString"
MOTOR_ST = "motor"

DIMM_TOPIC = f"{BASE_TOPIC}/{DIMM_ST}"
SPEED_TOPIC = f"{BASE_TOPIC}/{SPEED_ST}"
COLOR_TOPIC = f"{BASE_TOPIC}/{COLOR_ST}"
FG_COLOR_TOPIC = f"{BASE_TOPIC}/{FG_COLOR_ST}"
BG_COLOR_TOPIC = f"{BASE_TOPIC}/{BG_COLOR_ST}"
PATTERN_TOPIC = f"{BASE_TOPIC}/{PATTERN_ST}"
AUTO_TOPIC = f"{BASE_TOPIC}/{AUTO_ST}"
SHORT_STROBE_TOPIC = f"{BASE_TOPIC}/{SHORT_STROBE}"
STROBE_COLOR_TOPIC = f"{BASE_TOPIC}/{STROBE_COLOR}"
FG_COLOR_STRING_TOPIC = f"{BASE_TOPIC}/{FG_COLOR_STRING}"
BG_COLOR_STRING_TOPIC = f"{BASE_TOPIC}/{BG_COLOR_STRING}"
STROBE_COLOR_STRING_TOPIC = f"{BASE_TOPIC}/{STROBE_COLOR_STRING}"
MOTOR_TOPIC = f"{BASE_TOPIC}/{MOTOR_ST}"



#################### LIGHT STUFF
channels_per_lamp = 6
num_lights = 16

LIGHTS = LightGroup()
for i in range (0,16):
    light = Light(i * channels_per_lamp + 1)
    LIGHTS.add_light(light)

LIGHTS._upper_lights = [LIGHTS._lights[2], LIGHTS._lights[3], LIGHTS._lights[4], LIGHTS._lights[7], LIGHTS._lights[8], LIGHTS._lights[11], LIGHTS._lights[12], LIGHTS._lights[14]]
LIGHTS._lower_lights = [LIGHTS._lights[0], LIGHTS._lights[1], LIGHTS._lights[5], LIGHTS._lights[6], LIGHTS._lights[9], LIGHTS._lights[10], LIGHTS._lights[13], LIGHTS._lights[15]]


############## MQTT STUFF ################
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

def subscribe (client, topic):
    client.subscribe(topic)
    logger.info(f"Subscribing to {topic}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        client.bad_connection = False
    else:
        client.bad_connection = True
        client.connected_flag = False
    logger.info("Connected with result code " + str(rc))
    subscribe(client, DIMM_TOPIC)
    subscribe(client, SPEED_TOPIC)
    subscribe(client, COLOR_TOPIC)
    subscribe(client, FG_COLOR_TOPIC)
    subscribe(client, BG_COLOR_TOPIC)
    subscribe(client, PATTERN_TOPIC)
    subscribe(client, AUTO_TOPIC)
    subscribe(client, SHORT_STROBE_TOPIC)
    subscribe(client, STROBE_COLOR_TOPIC)
    subscribe(client, FG_COLOR_STRING_TOPIC)
    subscribe(client, BG_COLOR_STRING_TOPIC)
    subscribe(client, STROBE_COLOR_STRING_TOPIC)
    subscribe(client, MOTOR_TOPIC)
    

def on_message(client, userdata, msg):
    logger.info(msg.topic+" "+str(msg.payload))
    topic = msg.topic

    if topic == DIMM_TOPIC:
        handle_dimm(msg)
    elif topic == SPEED_TOPIC:
        handle_speed(msg)
    elif topic == COLOR_TOPIC:
        handle_color(msg)
    elif topic == FG_COLOR_TOPIC:
        handle_fg_color(msg)
    elif topic == BG_COLOR_TOPIC:
        handle_bg_color(msg)
    elif topic == PATTERN_TOPIC:
        handle_pattern(msg)
    elif topic == AUTO_TOPIC:
        handle_auto(msg)
    elif topic == SHORT_STROBE_TOPIC:
        handle_short_strobe(msg)
    elif topic == STROBE_COLOR_TOPIC:
        handle_strobe_color(msg)
    elif topic == FG_COLOR_STRING_TOPIC:
        handle_fg_color_string(msg)
    elif topic == BG_COLOR_STRING_TOPIC:
        handle_bg_color_string(msg)
    elif topic == STROBE_COLOR_STRING_TOPIC:
        handle_strobe_color_string(msg)
    elif topic == MOTOR_TOPIC:
        handle_motor(msg)
    
"""
##############################
UDP STUFF
##############################
"""
UDPSERVER = comm.spawn_udp_server()


"""
Outline:
[X] Connection Handling
[X] Error Handling (Reconnect after disconnect!)
[X] Make Topics configurable
[ ] Topics:
    - ColorFG DONE
    - ColorBG DONE
    - ColorMix 
    - Pattern DONE
    - Speed DONE
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

def limit_rgb(value):
    if value < 0:
        new_value = 0
    elif value > 255:
        new_value = 255
    else:
        new_value = value
    return new_value

def string_to_color(colorstring: str):
    """
    Returns Tuple (R, g, b) or None
    """
    # Check if we start with a (
    colorstring = colorstring.replace("(", "")
    colorstring = colorstring.replace(")", "")
    try:
        r,g,b = colorstring.split(",")
        r = limit_rgb(int(r))
        g = limit_rgb(int(g))
        b = limit_rgb(int(b))
        return (r,g,b)
    except ValueError:
        logger.warn("Wrong format for colorstring. r,g,b only.")
        return None


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
        if color_index >= len(list_of_colors):
            color_index = len(list_of_colors)-1
        elif color_index < 0:
            color_index = 0
        color_name, values = list_of_colors[color_index]
        logger.info(f"color: {color_name}\tvalues:{values}")
        return values
    except ValueError:
        # check if name is in dict:
        # we have a string in a dict, hopefully
        logger.warn("Invalid Value for color topic!")
        return None

def handle_dimm(message):
    try:
        new_value = float(message.payload)
        converted_value = new_value / MAXIMUM_MQTT_INT_VALUE
        if converted_value < 0:
            converted_value = 0
        elif converted_value > 1.0:
            converted_value = 1.0

        LIGHTS.set_global_dimmer(converted_value)
        logger.info(f"Set dimmer to {converted_value}")

    except ValueError:
        logger.warn("Invalid message passed to handle_dimm: {}".format(message.payload))

def handle_color(message):
    try:
        new_color = msg_to_color(message)
        LIGHTS._fg_color = new_color
        # TODO Write multiple fitting color schemes
        logger.info(f"Set color to {new_color}")

    except ValueError:
        logger.warn("Invalid message passed to handle_color: {}".format(message.payload))

def handle_fg_color(message):
    try:
        new_color = msg_to_color(message)
        LIGHTS._fg_color = new_color
        logger.info(f"Set fg_color to {new_color}")

    except ValueError:
        logger.warn("Invalid message passed to handle_color: {}".format(message.payload))

def handle_bg_color(message):
    try:
        new_color = msg_to_color(message)
        LIGHTS._bg_color = new_color
        logger.info(f"Set bg_color to {new_color}")

    except ValueError:
        logger.warn("Invalid message passed to handle_color: {}".format(message.payload))


def handle_pattern(message):
    try:
        pattern_number = int(message.payload)

        new_pattern = (pattern_number / MAXIMUM_MQTT_INT_VALUE) * len(Pattern)

        LIGHTS.set_pattern(new_pattern)
        logger.info(f"Set pattern to: {new_pattern}")

    except ValueError:
        logger.warn("Invalid message passed to handle_color: {}".format(message.payload))

def handle_speed(message):
    try:
        speed_number = int(message.payload)

        new_speed = (speed_number / MAXIMUM_MQTT_INT_VALUE)

        LIGHTS.set_speed(new_speed)
        logger.info(f"Set lights speed to {new_speed}")

    except ValueError:
        logger.warn("Invalid message passed to handle_speed: {}".format(message.payload))

def handle_auto(message):
    try:
        auto_number = int(message.payload)

        new_auto = (auto_number / MAXIMUM_MQTT_INT_VALUE) * 240


        if new_auto < 30:
            LIGHTS.auto_animation = False
            logger.info("Deactivated auto_animation.")
        else:
            LIGHTS.auto_animation = True
            LIGHTS.auto_beat = 60 / new_auto
            LIGHTS._beat_interval = 60 / new_auto
            logger.info("Activated auto_animation.")
        logger.info(f"Set auto_bpm to {new_auto}")

    except ValueError:
        logger.warn("Invalid message passed to handle_speed: {}".format(message.payload))

def handle_short_strobe(message):
    try:
        seconds = float(message.payload)
        LIGHTS.short_strobe(seconds)
        logger.info(f"Short Strobe for {seconds}")
    except ValueError:
        logger.warn("Invalid message passed to handle_short_strobe: {}".format(message.payload))

def handle_strobe_color(message):
    try:
        new_color = msg_to_color(message)
        LIGHTS._strobe_color = new_color
        logger.info(f"Set strobe_color to {new_color}")

    except ValueError:
        logger.warn("Invalid message passed to handle_strobe_color: {}".format(message.payload))

def handle_fg_color_string(message):
    try:
        message_string = str(message.payload.decode("utf-8"))
        logger.info(message_string)
        new_color = string_to_color(message_string)
        LIGHTS._fg_color = new_color
        logger.info(f"Set fg_color to {new_color}")
    except ValueError:
        logger.warn(f"Invalid message passed to handle_bg_color_string: {message_string}")
    except TypeError:
        logger.warn(f"Invalid message type passed to handle_bg_color_string: {type(message_string)}")

def handle_bg_color_string(message):
    try:
        message_string = str(message.payload.decode("utf-8"))
        logger.info(message_string)
        new_color = string_to_color(message_string)
        LIGHTS._bg_color = new_color
        logger.info(f"Set bg_color to {new_color}")
    except ValueError:
        logger.warn(f"Invalid message passed to handle_bg_color_string: {message_string}")
    except TypeError:
        logger.warn(f"Invalid message type passed to handle_bg_color_string: {type(message_string)}")

def handle_strobe_color_string(message):
    try:
        message_string = str(message.payload.decode("utf-8"))
        logger.info(message_string)
        new_color = string_to_color(message_string)
        LIGHTS._strobe_color = new_color
        logger.info(f"Set _strobe_color to {new_color}")
    except ValueError:
        logger.warn(f"Invalid message passed to handle_bg_color_string: {message_string}")
    except TypeError:
        logger.warn(f"Invalid message type passed to handle_bg_color_string: {type(message_string)}")
        
def handle_motor(message):
    try:
        value = int(message.payload)
        if value < 0:
            value = 0
        elif value > 255:
            value = 255
        LIGHTS.set_motor(value)
        logger.info(f"Motor set to {value}")
    except ValueError:
        logger.warn("Invalid message passed to handle_motor: {}".format(message.payload))



# The callback for when a PUBLISH message is received from the server.

if __name__ == "__main__":
    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection = False

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    client.loop_start()

    tries = 0
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except:
        client.bad_connection = True

    while True:
        logger.info("Waiting for MQTT connection...")
        sleep(3.0)
        if client.connected_flag:
            break
        elif client.bad_connection:
            logger.info("Trying again...")
            try:
                client.connect(MQTT_HOST, MQTT_PORT, 60)
            except:
                client.bad_connection = True

    logger.info("MQTT connected!")




    logger.info("Blinking now...")
    LIGHTS.set_pattern(Pattern.SOLID)
    LIGHTS.set_lights_color((0,255,0))
    LIGHTS.set_lights_dimmer(1.0)
    LIGHTS.render()
    sleep(0.5)
    LIGHTS.set_lights_dimmer(0.0)
    LIGHTS.render()
    sleep(0.5)
    LIGHTS.set_lights_dimmer(1.0)
    LIGHTS.render()
    sleep(0.5)
    LIGHTS.set_lights_dimmer(0.0)
    LIGHTS.render()
    sleep(0.5)
    LIGHTS.set_lights_dimmer(1.0)
    LIGHTS.render()
    sleep(0.5)
    LIGHTS.set_lights_dimmer(0.0)
    LIGHTS.render()
    logger.info("Lets go!")
    while True:
        try:
            LIGHTS.loop()
            beat = comm.beat_detected()
            if beat:
                LIGHTS.christophbeat()
        except KeyboardInterrupt:
            break



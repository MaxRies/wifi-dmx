### Plotting
import matplotlib as mpl
import matplotlib.pyplot as plt

light_positions_x = [
        0.3,
        1.2,
        2.2,
        3.2,
        4.3,
        5.2,
        3.1,
        1.1,
        -1.1,
        -3.1,
        -5.2,
        -4.3,
        -3.2,
        -2.2,
        -1.2,
        -0.3
    ]

light_positions_y = [
        5.5,
        3.9,
        2.2,
        0.4,
        -1.4,
        -3.0,
        -3.0,
        -3.0,
        -3.0,
        -3.0,
        -3.0,
        -1.4,
        0.4,
        2.2,
        3.9,
        5.5
    ]
light_size = 100

FPS = 30.0


def init_draw():
    draw_lights.ax, draw_lights.fig = plt.subplots()
    light_colors = [(i/16.0, 0.0, 1.0-i/16.0) for i in range(0,16) ]
    plt.scatter(light_positions_x, light_positions_y, c=light_colors, s=light_size)
    plt.draw()
    plt.pause(1)

def draw_lights(values):
    colors = [light.float_values for light in values]
    plt.clf()
    plt.scatter(light_positions_x, light_positions_y, c=colors, s=light_size)
    # plt.draw()
    plt.pause(0.01)

def draw_fade(rgb_array):
    steps = list(range(0, len(rgb_array)))
    values = [1 for i in range(0, len(rgb_array))]

    plt.plot(steps, values)
    for index, color in enumerate(rgb_array):
        plt.fill([index, index+1], [0,1], c=color)
    plt.show()
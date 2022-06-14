import colorsys

from plot_lights import draw_fade

COLORS = {
    'red' : [1.0, 0, 0],
    'green' : [0.0, 1.0, 0],
    'blue' : [0.0, 0.0, 1.0],
    'black': [0.0, 0.0, 0.0],
    'white': [1.0, 1.0, 1.0]
}


def calculate_bipolar_fade(color_1, color_2, size, symmetric = True, hsl_conversion=False):
    """
    Accepts two colors (can be black!) and calculates a fade between those two colors.
    Colors must be (r,g,b).
    Calculation happens in HLS colorspace.
    """
    if symmetric:
        if size % 2 == 1:
            size += 1
    
    if hsl_conversion:
        color_1_calc = colorsys.rgb_to_hls(color_1[0], color_1[1], color_1[2])
        color_2_calc = colorsys.rgb_to_hls(color_2[0], color_2[1], color_2[2])
    else:
        color_1_calc = color_1
        color_2_calc = color_2


    array = [[0,0,0] for i in range (0, size)]

    array[0] = color_1_calc

    if symmetric:
        array[int(size/2)] = color_2_calc

        # Gradients
        hue_gradient = (color_2_calc[0] - color_1_calc[0]) / (size/2)
        luminance_gradient = (color_2_calc[1] - color_1_calc[1]) / (size/2)
        saturation_gradient = (color_2_calc[2] - color_1_calc[2]) / (size/2)
        
        hsl_array = [(hue_gradient * i + color_1_calc[0], luminance_gradient * i + color_1_calc[1], saturation_gradient * i + color_1_calc[2]) for i in range (0, int(size/2))]
        hsl_array_extension = hsl_array[::-1]
        hsl_array.extend(hsl_array_extension)

    else:
        array[-1] = color_2_calc
        
        # Gradients
        hue_gradient = (color_2_calc[0] - color_1_calc[0]) / (size)
        luminance_gradient = (color_2_calc[1] - color_1_calc[1]) / (size)
        saturation_gradient = (color_2_calc[2] - color_1_calc[2]) / (size)

        hsl_array = [(hue_gradient * i + color_1_calc[0], luminance_gradient * i + color_1_calc[1], saturation_gradient * i + color_1_calc[2]) for i in range (0, int(size))]
        
    if hsl_conversion:
        rgb_array = [colorsys.hls_to_rgb(*value) for value in hsl_array]
    else:
        rgb_array = hsl_array
        
    return rgb_array


if __name__ == "__main__":
    rgb_arr_symm_hsl = calculate_bipolar_fade(COLORS['black'], COLORS['red'], size=264, symmetric = False, hsl_conversion=True)
    rgb_arr_no_hsl = calculate_bipolar_fade(COLORS['black'], COLORS['red'], size=264, symmetric = False, hsl_conversion=False)

    print(rgb_arr_symm_hsl)
    draw_fade(rgb_array=rgb_arr_symm_hsl)
    print(rgb_arr_no_hsl)
    draw_fade(rgb_array=rgb_arr_no_hsl)
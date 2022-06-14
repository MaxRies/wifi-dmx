from matplotlib.colors import LightSource
from wifidmx.light import Light

def test_set_color():
    l1 = Light()
    l1.color = (255, 0, 0)
    assert l1.scaled_values == (255, 0,0)
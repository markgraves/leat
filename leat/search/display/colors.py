"""Color utilities"""

from .color_constants import CSS3_NAMES_TO_HEX

def mix_hex_color_strings(color_a, color_b=None, t=0.5, gamma=2.2):
    "Mix two colors by hex values or CSS3 names"
    # See https://stackoverflow.com/questions/726549/algorithm-for-additive-color-mixing-for-rgb-values
    def hex_to_float(h, color_missing=None):
        """Convert a hex rgb string (e.g. #ffffff) to an RGB tuple (float, float, float)."""
        if h[0] != '#':
            hex = CSS3_NAMES_TO_HEX.get(h, None)
            if hex is None:
                print('Warning:', 'Unknown color name', h)
                return color_missing
            h = hex
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (1, 3, 5))  # skip '#'

    def float_to_hex(rgb):
        """Convert an RGB tuple or list to a hex RGB string."""
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    if color_b is None:
        assert not isinstance(color_a, str)
        if len(color_a) == 1:
            return color_a[0]
        floats = [hex_to_float(h, (0, 0, 0)) for h in color_a]
        rgb = [
            pow(sum((1 / len(floats)) * c[i] ** gamma for c in floats), 1 / gamma)
            for i in (0, 1, 2)
        ]
        # print(color_a, floats, rgb)
    else:
        a = hex_to_float(color_a)
        if a is None:
            return color_b
        b = hex_to_float(color_b)
        if b is None:
            return color_a
        rgb = [
            pow((1 - t) * a[i] ** gamma + t * b[i] ** gamma, 1 / gamma)
            for i in (0, 1, 2)
        ]
    return float_to_hex(rgb)

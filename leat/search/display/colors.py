"""Color utilities"""

import html
from typing import Optional

from .color_constants import CSS3_NAMES_TO_HEX


def mix_hex_color_strings(
    color_a: str, color_b: Optional[str] = None, t: float = 0.5, gamma: float = 2.2
) -> tuple:
    """
    Mix two or more colors by hex values or CSS3 names

    Args:
      color_a: str: Color to mix (hex value or CSS3 name)
      color_b: str | None: If None, color_a is a list of colors Color to mix (Default value = None)
      t: float:  Mixing threshold (weighting of color b) (Default value = 0.5)
      gamma: float: Gamma correction (Default value = 2.2)

    Returns:
      RGB tuple of mixed colors
    """
    # See https://stackoverflow.com/questions/726549/algorithm-for-additive-color-mixing-for-rgb-values
    def hex_to_float(h: str, color_missing: Optional[str] = None):
        """
        Convert a hex rgb string (e.g. #ffffff) to an RGB tuple (float, float, float).

        Args:
          h: str: HEX RGB string, or the name of a color in CSS3
          color_missing: str | None: Value to return if named color does not exist (Default value = None)

        Returns:
          tuple: RGB values [0, 1]
        """
        if h[0] != "#":
            hex = CSS3_NAMES_TO_HEX.get(h.lower(), None)
            if hex is None:
                print("Warning:", "Unknown color name", h)
                return color_missing
            h = hex
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (1, 3, 5))  # skip '#'

    def float_to_hex(rgb: tuple) -> str:
        """
        Convert an RGB tuple or list to a hex RGB string.

        Args:
          rgb: tuple: RGB values [0, 1]

        Returns:
          str: HEX string corresponding to tuple
        """
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


def color_dict_legend(color_dict: dict) -> str:
    """
    Create a html legend for a color dict

    Args:
      color_dict: dict: Dictionary of keys and colors

    Returns:
      str: HTML div with keys listed in its associated color
    """
    result = "<div>\n"
    for concept, color in color_dict.items():
        result += f'<span style="background-color: {color}">&emsp;</span> '
        result += f'<u style="color: {color}">' + html.escape(concept) + "</u><br/>"
    result += "</div>"
    return result
